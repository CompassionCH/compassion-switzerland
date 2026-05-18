"""
auth_external — res.users extension for JWT-based authentication.

Issues HS256 JWT access + refresh tokens for external (typically SPA)
clients, and lets those clients authenticate later RPC calls via a
`Bearer` token in the `Authorization` header.

Token-family / reuse-detection semantics live in `refresh_tokens.py`;
this file is only signing, verification and the `_check_credentials`
override that lets a Bearer token replace the password.
"""

import base64
import contextlib
import logging
import re
import secrets
import threading
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt import (
    DecodeError,
    ExpiredSignatureError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
)

from odoo import api, models, tools
from odoo.exceptions import AccessDenied
from odoo.tools import config

_logger = logging.getLogger(__name__)

authorization_extractor = re.compile(r'(\w+)[:=] ?"?(\w+)"?')

USER_ACCESS_AUD = "user_auth_grant"
USER_REFRESH_AUD = "user_refresh_grant"
JWT_ALG = "HS256"


def gen_signing_key() -> bytes:
    """Return the raw HMAC key used to sign/verify JWTs.

    Prefers `odoo.conf` `[options] auth_external.jwt_key` (UTF-8 string).
    Falls back to an ephemeral 256-byte random secret per process — which
    invalidates every issued token on Odoo restart. Suitable only for
    dev; production must set the config value.

    Why 256 bytes: HS256 only needs >= 32 bytes (RFC 7518 §3.2), but we
    use 256 to leave plenty of margin. PyJWT will accept any non-empty
    bytes value for the secret.
    """
    conf_key = config.get("auth_external.jwt_key")
    if conf_key:
        return conf_key.encode("utf-8")
    secret = secrets.token_bytes(256)
    _logger.warning(
        "No JWT key found in config, generating an ephemeral one. "
        "Set `auth_external.jwt_key = <random string>` in odoo.conf to "
        "make tokens survive restarts. The current ephemeral key is "
        "logged at DEBUG level."
    )
    _logger.debug("auth_external ephemeral JWT key (base64): %s",
                  base64.b64encode(secret).decode("ascii"))
    return secret


# Module-level keys — generated once per process.
# *** Tokens issued before a restart are invalidated when the ephemeral
# key is regenerated. *** Set `auth_external.jwt_key` in odoo.conf to
# avoid this in production.
access_token_signing_key = gen_signing_key()
refresh_token_signing_key = gen_signing_key()


class InvalidTotp(AccessDenied):
    """Raised when a TOTP code is missing or wrong in a single-shot
    (login + password + totp) authentication call. The controller's
    `_authenticate_with_optional_totp` helper raises this; we keep it
    here for callers that still want to distinguish it from a regular
    AccessDenied."""
    pass


class ExternalAuthUsers(models.Model):
    _inherit = "res.users"
    _description = "Adds authentication for users from external platforms."

    # --------------------------------------------------------------- #
    # JWT signing / verification                                       #
    # --------------------------------------------------------------- #

    def _generate_jwt(
        self,
        iss: str,
        sub: Any,
        aud: str,
        exp: datetime,
        key: bytes,
    ) -> tuple[dict, str]:
        """Generate a JWT signed with HS256.

        :param iss: issuer (typically the Odoo host).
        :param sub: subject (the user id we're issuing the token for).
        :param aud: audience — one of USER_ACCESS_AUD / USER_REFRESH_AUD.
        :param exp: expiration datetime (timezone-aware).
        :param key: raw HMAC secret bytes.
        :return: (payload, encoded_token) tuple.
        """
        now = datetime.now(timezone.utc)
        # `sub` is coerced to str: RFC 7519 §4.1.2 mandates string
        # subjects and PyJWT rejects non-strings on decode. Callers
        # (refresh / verify) must cast back to int when comparing
        # with a uid.
        payload = {
            # RFC 7519 §4.1 standard claims
            "iss": iss,
            "sub": str(sub),
            "aud": aud,
            "exp": int(exp.timestamp()),
            "nbf": int(now.timestamp()),
            "iat": int(now.timestamp()),
            "typ": "JWT",
            # `jti` makes every token unique so two tokens minted in the
            # same second don't collide.
            "jti": str(uuid.uuid4()),
        }
        token = jwt.encode(payload, key, algorithm=JWT_ALG)
        return payload, token

    def _parse_jwt_token(
        self,
        token: str,
        sub: Any,
        iss: str,
        aud: str,
        key: bytes,
    ) -> dict:
        """Verify a JWT and return its payload.

        :param token: raw token string from the wire.
        :param sub: expected subject (uid). Pass None to skip the sub
            check (used when refreshing — we want the payload to learn
            who the token belongs to before the user is known).
        :param iss: expected issuer.
        :param aud: expected audience.
        :param key: raw HMAC secret bytes for verification.
        :return: the decoded payload as a dict.
        :raises AccessDenied: on any verification failure (bad signature,
            expired, wrong audience, wrong issuer, missing claims).
        """
        try:
            # PyJWT validates exp, nbf, iat, audience, issuer inline.
            # We pass `options={"require": [...]}` to enforce presence
            # of the standard claims even though the encoder always sets
            # them — defence-in-depth against tokens crafted with the
            # right key but missing claims.
            payload = jwt.decode(
                token,
                key,
                algorithms=[JWT_ALG],
                audience=aud,
                issuer=iss,
                options={
                    "require": ["exp", "iss", "sub", "aud", "iat"],
                    "verify_signature": True,
                    "verify_exp": True,
                    "verify_nbf": True,
                    "verify_aud": True,
                    "verify_iss": True,
                },
            )
        except ExpiredSignatureError as exc:
            _logger.info("JWT expired: %s", exc)
            raise AccessDenied() from exc
        except (
            InvalidAudienceError,
            InvalidIssuerError,
            DecodeError,
            InvalidTokenError,
        ) as exc:
            _logger.info("JWT validation failed: %s", exc)
            raise AccessDenied() from exc

        # PyJWT verifies `aud` and `iss` inline but has no `subject=`
        # option, so we check `sub` ourselves. `sub` is always a
        # string in the payload (see _generate_jwt); cast the
        # expected value for comparison.
        if sub is not None and payload.get("sub") != str(sub):
            _logger.info("JWT subject mismatch")
            raise AccessDenied()

        return payload

    # --------------------------------------------------------------- #
    # Token lifecycle for external clients                             #
    # --------------------------------------------------------------- #

    def generate_external_auth_tokens(self, rt_old=None):
        """Generate a new access + refresh token pair for self.

        :param rt_old: if provided, the refresh token currently held by
            the caller. It will be revoked (rotated) before the new pair
            is issued. If `rt_old` has already been rotated (= replay
            attack or buggy client), the entire token family is revoked.
        :return: {"access_token": str, "refresh_token": str,
                  "expires_at": iso8601}
        :raises AccessDenied: when the caller isn't allowed to issue
            tokens for `self`, or when a replay is detected.

        Reuse-detection side effect:
            When a replay is detected, this method commits the
            in-flight transaction (`self.env.cr.commit()`) before
            raising AccessDenied, the family revocation must
            survive the rollback the raise would otherwise trigger.
            Any other pending writes on the cursor will also be
            committed early. The only caller today (the
            `/auth/refresh` controller) has no other pending writes
            at this point; avoid invoking this method from non-HTTP
            contexts (cron, XMLRPC) that hold unrelated in-flight
            state.
        """
        self.ensure_one()

        # Can only generate auth tokens for self.
        if self.env.user.id != self.id:
            _logger.info(
                "User '%s' (%d) tried to generate an auth token for user "
                "with id %d.",
                self.env.user.login, self.env.user.id, self.id,
            )
            raise AccessDenied()

        # Issuing brand-new tokens (no rt_old) requires password auth,
        # not Bearer auth. Otherwise a stolen access token could be used
        # to mint fresh ones, bypassing refresh-token rotation.
        auth_header = getattr(
            threading.current_thread(), "auth_external_authorization", "",
        )
        if auth_header.startswith("Bearer ") and rt_old is None:
            _logger.info(
                "User '%s' tried to refresh their auth token while being "
                "authenticated with an auth token.", self.login,
            )
            raise AccessDenied()

        refresh_tokens = self.env["auth_external.refresh_tokens"]
        rt_old_model = None
        if rt_old is not None:
            rt_old_payload = self._check_refresh_token(rt_old, self.env.user.id)
            rt_old_model = refresh_tokens.sudo().get_by_jti(rt_old_payload["jti"])
            if rt_old_model is None:
                # A valid-looking JWT whose jti has no DB row means the
                # token was deleted server-side after issuance — treat
                # as compromised.
                raise AccessDenied()

            if rt_old_model.is_revoked:
                user_id = rt_old_payload["sub"]
                rt_old_model.sudo().revoke_family()
                # Commit so the revocation survives the raise.
                self.env.cr.commit()
                _logger.warning(
                    "[RTRD] Refresh Token Reuse Detection: jti=%s user_id=%s "
                    "— revoking the whole token family. Either an attacker "
                    "is replaying a stolen token, or a client-side bug "
                    "reused a rotated token.",
                    rt_old_model.jti, user_id,
                )
                raise AccessDenied()
            rt_old_model.ensure_one()
            rt_old_model.sudo().revoke()

        # All checks passed — mint the new pair.
        tokens_config = (
            self.env["auth_external.tokens_config"].sudo().get_singleton()
        )

        now_utc = datetime.now(timezone.utc)
        at_new_exp = now_utc + timedelta(
            hours=tokens_config.access_token_duration_hours
        )
        rt_new_exp = now_utc + timedelta(
            days=tokens_config.refresh_token_duration_days
        )

        at_new_payload, at_new = self._generate_jwt(
            tokens_config.issuer_id,
            self.env.user.id,
            USER_ACCESS_AUD,
            at_new_exp,
            access_token_signing_key,
        )
        rt_new_payload, rt_new = self._generate_jwt(
            tokens_config.issuer_id,
            self.env.user.id,
            USER_REFRESH_AUD,
            rt_new_exp,
            refresh_token_signing_key,
        )

        # Persist the new refresh-token row. Odoo stores Datetime fields
        # as naive UTC, so strip the tz.
        rt_new_model = refresh_tokens.sudo().create({
            "jti": rt_new_payload["jti"],
            "exp": rt_new_exp.replace(tzinfo=None),
            "user_id": self.env.user.id,
        })
        if rt_old is not None:
            rt_old_model.link_child(rt_new_model)

        access_token_exp_str = at_new_exp.isoformat()
        _logger.info(
            "Generated new tokens for user '%s'. Access token expires in "
            "%d hours (%s).",
            self.login,
            tokens_config.access_token_duration_hours,
            access_token_exp_str,
        )

        return {
            "access_token": at_new,
            "refresh_token": rt_new,
            "expires_at": access_token_exp_str,
        }

    def _check_refresh_token(self, token: str, sub: Any) -> dict:
        """Validate a refresh-token JWT and return its payload."""
        tokens_config = (
            self.env["auth_external.tokens_config"].sudo().get_singleton()
        )
        return self._parse_jwt_token(
            token,
            sub,
            tokens_config.issuer_id,
            USER_REFRESH_AUD,
            refresh_token_signing_key,
        )

    def _check_access_token(self, token: str) -> None:
        """Validate an access-token JWT against the current request user."""
        tokens_config = (
            self.env["auth_external.tokens_config"].sudo().get_singleton()
        )
        try:
            self._parse_jwt_token(
                token,
                self.env.user.id,
                tokens_config.issuer_id,
                USER_ACCESS_AUD,
                access_token_signing_key,
            )
        except AccessDenied:
            _logger.info(
                "User '%s' failed to validate access token.",
                self.env.user.login,
            )
            raise

    def _check_credentials(self, credential, env):
        # Bearer-token shortcut: a valid JWT access token bypasses the
        # password check entirely. The Translation Platform home page
        # loads in <2s vs <4s with this in place.
        #
        # The header is read from a thread-local rather than from
        # request.httprequest.headers: XMLRPC dispatch unbinds the
        # request via odoo.http.borrow_request(), so the request proxy
        # is inaccessible from here on the RPC path. ir_http._dispatch
        # stashes the header in the thread before dispatch — see
        # models/ir_http.py.
        authorization_header = getattr(
            threading.current_thread(),
            "auth_external_authorization", "",
        )
        if authorization_header.startswith("Bearer "):
            token = authorization_header.split(" ", 1)[1]
            try:
                self._check_access_token(token)
                # mfa=skip: the access token was issued only after a
                # successful (password + TOTP) auth, so MFA does not
                # need to be re-checked at this layer.
                return {
                    "uid": self.env.user.id,
                    "auth_method": "jwt_bearer",
                    "mfa": "skip",
                }
            except AccessDenied:
                # The Authorization header may belong to a different
                # consumer of res.users — fall through to the standard
                # password / OAuth chain.
                pass

        return super()._check_credentials(credential, env)

    @classmethod
    def check(cls, db, uid, passwd):
        # The webapp sends a dummy `passwd="None"` paired with an
        # `Authorization: Bearer <jwt>` header. The cached base check
        # is keyed on (uid, passwd) and would always reject the dummy
        # password; short-circuit by validating the JWT directly and
        # returning before the cache is consulted at all.
        #
        # The header is read from the thread-local stash for the same
        # reason as in _check_credentials (XMLRPC unbinds request).
        authorization_header = getattr(
            threading.current_thread(),
            "auth_external_authorization", "",
        )
        if authorization_header.startswith("Bearer "):
            token = authorization_header.split(" ", 1)[1]
            with contextlib.closing(cls.pool.cursor()) as cr:
                env = api.Environment(cr, uid, {})
                user = env["res.users"].browse(uid)
                if not user.exists() or not user.active:
                    raise AccessDenied()
                try:
                    user._check_access_token(token)
                    return  # success — absence of exception = auth ok
                except AccessDenied:
                    # Header may be for some other consumer; fall
                    # through to the password path.
                    pass

        if not passwd:
            raise AccessDenied()
        return super().check(db, uid, passwd)
