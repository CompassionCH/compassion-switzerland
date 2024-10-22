import contextlib
import logging
import re
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid

from jwt import JWT, AbstractJWKBase, supported_key_types
from jwt.exceptions import JWTDecodeError
from jwt.utils import get_int_from_datetime

from odoo import api, models
from odoo.exceptions import AccessDenied
from odoo.http import request

from odoo.addons.base.models.res_users import Users

_logger = logging.getLogger(__name__)

authorization_extractor = re.compile(r'(\w+)[:=] ?"?(\w+)"?')

# TODO: move those to settings.
issuer_id = "compassion.ch"
access_token_duration_seconds = 60 * 60 * 3  # Token is only valid for this period of time.
refresh_token_duration_seconds = 60 * 60 * 24 * 28
user_access_aud = "user_auth_grant"
user_refresh_aud = "user_refresh_grant"

def gen_signing_key() -> AbstractJWKBase:
    """Generates a cryptographically secure random signing/verification key, which needs to
    be used in HMAC.
    
    Regarding the secret size:
    "A key of the same size as the hash output (for instance, 256 bits for
    "HS256") or larger MUST be used with this algorithm.  (This
    requirement is based on Section 5.3.4 (Security Effect of the HMAC
    Key) of NIST SP 800-117 [NIST.800-107], which states that the
    effective security strength is the minimum of the security strength
    of the key and two times the size of the internal hash value.)"
    https://www.rfc-editor.org/rfc/rfc7518#section-3.2

    Returns:
        AbstractJWKBase: generated signing key.
    """
    # As we are using HS256 as the signing algorithm, we need 512 bits of entropy.
    # To be safe, we use 2048 bits (=256*8) which will be hashed down anyway
    secret = secrets.token_bytes(256)
    return supported_key_types()["oct"](secret)


# We use symmetric signing/verification keys as only the server needs to sign and verify tokens.
# The keys are stored in program memory to avoid the difficult problem of storing secrets.
# *** This means that on server restart, all clients will have to login again ***
access_token_signing_key = gen_signing_key()
"""
Secret key used to sign/verify access_tokens
"""
refresh_token_signing_key = gen_signing_key()
"""
Secret key used to sign/verify refresh_tokens
"""

JWT_ALG = "HS256"

class InvalidTotp(AccessDenied):
    pass


class ExternalAuthUsers(models.Model):
    _inherit = "res.users"

    def _generate_jwt(
        self, iss: str, sub: any, aud: str, exp: datetime, key: AbstractJWKBase
    ):
        """
        Generates a new JWT,
        :param iss: the JWT issuer.
        :param sub: the JWT subject.
        :param aud: The JWT audience.
        :param exp: The JWT expiration date.
        :param key: The key to sign the JWT.
        :return: the JWT payload and token.
        """
        payload = {
            # Claims defined in RFC7529#section-4.1
            "iss": iss,
            "sub": sub,
            "aud": aud,
            "exp": get_int_from_datetime(exp),
            "nbf": get_int_from_datetime(datetime.now()),
            "iat": get_int_from_datetime(datetime.now()),
            "typ": "JWT",
            # Generate a random UUID (uuid4()).
            # This makes every token unique. Without this, two tokens generated
            # in the same second have the same value
            "jti": str(uuid.uuid4()),
        }

        token = JWT().encode(payload, key, alg=JWT_ALG)

        return payload, token

    def generate_external_auth_token(self, refresh_token=None):
        """Generates a new access token and refresh token for the user.
        :param refresh_token: the token allowing refreshing auth tokens.
        :returns: the freshly generated tokens.
        :raises AccessDenied: if the user can't generate tokens.
        """
        self.ensure_one()

        # Can only generate auth token for themselves.
        if self.env.user.id != self.id:
            _logger.info(
                "User '%s' (%d) tried to generate an auth token for user with id %d."
                % (
                    self.env.user.login,
                    self.env.user.id,
                    self.id,
                )
            )
            raise AccessDenied

        # Can't generate new tokens if user is authenticated using a token and
        # no refresh token is provided.
        # Require password authentication for token creation without refresh
        # token.
        if (
            "Authorization" in request.httprequest.headers
            and request.httprequest.headers["Authorization"].startswith("Bearer ")
            and refresh_token is None
        ):
            _logger.info(
                "User '%s' tried to refresh their auth token while being"
                " authenticated with an auth token." % self.login
            )
            raise AccessDenied

        # Verify the validity of the refresh token if one is provided.
        if refresh_token is not None:
            self._check_refresh_token(refresh_token, self.env.user.id)

            # TODO: revoke refresh_token as it was just used.
            # -> This cannot be done. It requires revocation list support. To impl?

        # Verification succeeded, we generate tokens.

        # https://stackoverflow.com/a/39079819
        current_timezone = datetime.now(timezone.utc).astimezone().tzinfo
        # We use a timestamp with time zone information to avoid ambiguity for
        # the expiration time of the tokens
        now = datetime.now(current_timezone)
        access_token_exp = now + timedelta(seconds=access_token_duration_seconds)
        # TODO: this is not good, it essentially makes refresh tokens have an infinite lifetime
        refresh_token_exp = now + timedelta(seconds=refresh_token_duration_seconds)

        payload, new_token = self._generate_jwt(
            issuer_id,
            self.env.user.id,
            user_access_aud,
            access_token_exp,
            access_token_signing_key,
        )

        # TODO : if the refresh_token is provided, DO NOT generate a new refresh_token to allow it to expire
        refresh_payload, new_refresh_token = self._generate_jwt(
            issuer_id,
            self.env.user.id,
            user_refresh_aud,
            refresh_token_exp,
            refresh_token_signing_key,
        )

        access_token_exp_str = access_token_exp.isoformat()

        _logger.info(
            "Generated new tokens for user '%s'. "
            "Access token expires in %d seconds (%s)"
            % (
                self.login,
                access_token_duration_seconds,
                access_token_exp_str,
            )
        )

        return {
            "access_token": new_token,
            "refresh_token": new_refresh_token,
            "expires_at": access_token_exp_str,
        }

    @classmethod
    def _check_refresh_token(cls, token: str, sub: any) -> dict:
        """Verifies the validity of a JWT for access token refresh.
        :param token: The token to check for validity.
        :returns: None if the token is valid.
        :raises AccessDenied: if the token is invalid.
        """
        try:
            return cls._parse_jwt_token(
                token,
                sub,
                issuer_id,
                user_refresh_aud,
                refresh_token_signing_key,
            )
        except AccessDenied as ex:
            raise ex

    def _check_access_token(self, token: str):
        """Verifies the validity of a JWT for authentication.
        :param token: The token to check for validity.
        :returns: None if the token is valid.
        :raises AccessDenied: if the token is invalid.
        """
        try:
            self._parse_jwt_token(
                token,
                self.env.user.id,
                issuer_id,
                user_access_aud,
                access_token_signing_key,
            )
        except AccessDenied as ex:
            _logger.info(
                "User '%s' failed to validate access token." % self.env.user.login
            )
            raise ex

    @classmethod
    def _parse_jwt_token(
        cls, token, sub: Any, iss: str, aud: str, key: AbstractJWKBase
    ) -> dict:
        """Verifies the validity of a JWT.
        :param token: The token to check for validity.
        :param sub: The expected subject of the JWT. Pass None to skip the check.
        :param iss: The expected issuer ID for the JWT.
        :param aud: The expected audience for the JWT.
        :returns: The payload if the check succeeded.
        :raises AccessDenied: if the token is invalid.
        """
        try:
            # Check the signature and expiration time of token
            payload = JWT().decode(token, key, algorithms={JWT_ALG}, do_verify=True, do_time_check=True)
        except JWTDecodeError as exc:
            _logger.info(
                "JWT check failed: %s", exc.__cause__ if exc.__cause__ else exc
            )
            raise AccessDenied from exc

        if "sub" not in payload or "iss" not in payload or "aud" not in payload:
            _logger.info("JWT is missing required entries")
            raise AccessDenied

        if payload["aud"] != aud or payload["iss"] != iss:
            _logger.info("JWT has mismatched fields")
            raise AccessDenied

        # We might not know the subject, until is it decoded from the payload.
        if sub is not None and payload["sub"] != sub:
            _logger.info("JWT subject mismatch")
            raise AccessDenied

        return payload

    def _check_credentials(self, password: str, user_agent_env) -> None:
        """Overrides the default method in res.users to accept authorization via a valid JWT access_token.
        If no access_token is found, defaults to password authentication.

        Args:
            password (str): Password used as fallback if no Authorization header with a valid JWT access_token is present in the request headers.
            user_agent_env (dict): additional credential data. This is used to provide the totp_token in 2FA.

        Raises:
            InvalidTotp: If the provided totp code is invalid.
            AccessDenied: If the credentials are incorrect.
        """
        # Check for Bearer *before* parent to prevent costly password check
        # when we are trying to authenticate using Bearer.
        # Consequence: Translation Platform home page loads in <2s vs <4s.
        try:
            if "Authorization" in request.httprequest.headers:
                authorization_header = request.httprequest.headers["Authorization"]

                # Bearer token login attempt.
                if authorization_header.startswith("Bearer "):
                    token = authorization_header.split(" ")[1]
                    self._check_access_token(token)

                    return self.env.user.id
        except AccessDenied:
            # Might have caught an authorization request from another service.
            # Delegate check to parent if that is the case.
            pass

        try:
            return super(ExternalAuthUsers, self)._check_credentials(
                password, user_agent_env
            )
        except AccessDenied:
            pass

        # Username / password + TOTP login attempt.
        if "totp" in user_agent_env and self.env.user.totp_enabled:
            Users._check_credentials(self, password, user_agent_env)

            try:
                totp = int(re.sub(r"\s", "", user_agent_env["totp"]))
                self.env.user._totp_check(totp)
                return # successful check
            except (AccessDenied, ValueError) as ex:
                raise InvalidTotp from ex

        raise AccessDenied

    @classmethod
    def check(cls, db, uid, passwd):
        if not passwd:
            raise AccessDenied()
        with contextlib.closing(cls.pool.cursor()) as cr:
            self = api.Environment(cr, uid, {})[cls._name]
            with self._assert_can_auth():
                if not self.env.user.active:
                    raise AccessDenied()

                # Users.check() is orm-cached on (username, password).

                if (
                    # Can't use cache on username/password as TOTP changes frequently.
                    self.env.user.totp_enabled
                    or
                    # Can't use cache if we are using an Authorization header
                    # as token might expire, and we are not using the password.
                    "Authorization" in request.httprequest.headers
                ):
                    super(ExternalAuthUsers, cls).check.clear_cache(self.env.user)

                return super(ExternalAuthUsers, cls).check(db, uid, passwd)
