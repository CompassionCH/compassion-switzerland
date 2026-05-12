##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
##############################################################################
# auth_external: HTTP endpoints for the external webapp.
#
# Three JSON endpoints, all auth="none", csrf=False, cors="*":
#   POST /auth/login    {login, password, totp}        → token pair
#   POST /auth/refresh  {refresh_token}                → rotated pair
#   POST /auth/logout   {refresh_token}                → revoke family
#
# /auth/login accepts a single-shot {login, password, totp} body — the
# password check and the TOTP check are sequenced internally so the
# external API stays a one-round trip.
##############################################################################
import logging
from typing import List, Tuple

from odoo.exceptions import AccessDenied
from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)


AUTH_LOGIN_ROUTE = "/auth/login"
AUTH_REFRESH_ROUTE = "/auth/refresh"
AUTH_LOGOUT_ROUTE = "/auth/logout"


class AuthController(Controller):
    def _validate_fields_as_expected(self, fields: List[str], data: dict) -> None:
        """Reject the request if `data` does not contain *exactly* the
        expected `fields` (no more, no less)."""
        for f in fields:
            if f not in data:
                _logger.info(
                    "Request failed because field '%s' was missing from "
                    "the request data", f,
                )
                raise AccessDenied()
        if len(fields) != len(data):
            _logger.info("Unexpected fields provided in request, expected %s", fields)
            raise AccessDenied()

    @route(
        route=AUTH_LOGIN_ROUTE,
        auth="none",
        type="json",
        methods=["POST"],
        csrf=False,
        cors="*",
        # readonly=False: these endpoints write (refresh_tokens.create,
        # revoke_*); without the explicit flag HttpCase test runs land
        # in a readonly transaction and the INSERT fails.
        readonly=False,
    )
    def login(self):
        payload = request.get_json_data()
        self._validate_fields_as_expected(["login", "password", "totp"], payload)
        login = payload["login"]
        password = payload["password"]
        totp = payload["totp"]

        # The password check is run via _check_credentials on the
        # current request cursor rather than via res_users.authenticate,
        # because authenticate() opens its own cursor from the pool —
        # that nested r/w open is rejected when the outer (HttpCase)
        # transaction is readonly.
        Users = request.env["res.users"].sudo()
        user = Users.search([("login", "=", login)], limit=1)
        if not user:
            _logger.info("Login failed: unknown user %r", login)
            raise AccessDenied()

        # env={"interactive": True}: auth_totp blocks password auth
        # for 2FA users when interactive=False (RPC-API-keys-only
        # enforcement). We do collect the TOTP code in the same
        # request and check it below, so the password step is
        # legitimately interactive here.
        user_in_self_env = user.with_user(user)
        try:
            user_in_self_env._check_credentials(
                {"login": login, "password": password, "type": "password"},
                {"interactive": True},
            )
        except AccessDenied:
            _logger.info("Login failed: bad password for %r", login)
            raise

        if user.totp_enabled:
            from ..models.res_users import InvalidTotp
            if not totp:
                _logger.info(
                    "Login denied for user %r: TOTP code required.", login,
                )
                raise InvalidTotp()
            try:
                user._totp_check(int(totp))
            except (AccessDenied, ValueError) as exc:
                # Bad / malformed TOTP surfaces as InvalidTotp (a
                # subclass of AccessDenied) so callers can distinguish
                # "wrong code" from "wrong password".
                raise InvalidTotp() from exc

        # Token generation runs in the user's own env, not sudo.
        user_id = user.id
        user_self = request.env["res.users"].with_user(user_id).browse(user_id)
        return {
            "user_id": user_id,
            "auth_tokens": user_self.generate_external_auth_tokens(),
        }

    def _validate_refresh_token(self, request) -> Tuple[str, dict]:
        """Validate that the request carries an authentic refresh token.

        :raises AccessDenied: if the body lacks `refresh_token`, or the
            token fails signature/expiration checks.
        :return: (raw_token_string, decoded_payload_dict).
        """
        payload_in = request.get_json_data()
        self._validate_fields_as_expected(["refresh_token"], payload_in)
        refresh_token = payload_in["refresh_token"]
        if refresh_token is None:
            raise AccessDenied()
        res_users = request.env["res.users"]
        return refresh_token, res_users._check_refresh_token(refresh_token, None)

    @route(
        route=AUTH_REFRESH_ROUTE,
        auth="none",
        type="json",
        methods=["POST"],
        csrf=False,
        cors="*",
        # readonly=False: these endpoints write (refresh_tokens.create,
        # revoke_*); without the explicit flag HttpCase test runs land
        # in a readonly transaction and the INSERT fails.
        readonly=False,
    )
    def refresh(self):
        refresh_token, payload = self._validate_refresh_token(request)

        # JWT `sub` is a string per RFC 7519 §4.1.2; cast back to int
        # to browse the user record.
        try:
            user_id = int(payload["sub"])
        except (TypeError, ValueError):
            _logger.error("Issued a refresh token with an invalid subject.")
            raise AccessDenied() from None

        user = request.env["res.users"].sudo().browse(user_id)
        user = user.with_user(user)  # exit sudo
        return user.generate_external_auth_tokens(refresh_token)

    @route(
        route=AUTH_LOGOUT_ROUTE,
        auth="none",
        type="json",
        methods=["POST"],
        csrf=False,
        cors="*",
        # readonly=False: these endpoints write (refresh_tokens.create,
        # revoke_*); without the explicit flag HttpCase test runs land
        # in a readonly transaction and the INSERT fails.
        readonly=False,
    )
    def logout(self):
        _, payload = self._validate_refresh_token(request)

        # The refresh token is authentic and non-expired but may already
        # have been revoked. In either case (legitimate logout, or
        # attacker calling logout after stealing a token) we revoke the
        # whole family — no harm done if the token was already revoked.
        refresh_tokens = request.env["auth_external.refresh_tokens"]
        jti = payload["jti"]
        user_id = payload["sub"]
        rt_model = refresh_tokens.sudo().get_by_jti(jti)
        if rt_model is None:
            _logger.warning(
                "user_id=%s requested logout but the refresh token "
                "(jti=%s) was not found in the database. Very strange.",
                user_id, jti,
            )
            raise AccessDenied()

        if rt_model.is_revoked:
            _logger.warning(
                "[RTRD] Refresh Token Reuse Detection on logout "
                "(jti=%s, user_id=%s). We're about to revoke the family "
                "anyway, but this is worrying — possible XSS exploit.",
                jti, user_id,
            )

        rt_model.sudo().revoke_family()
        return True
