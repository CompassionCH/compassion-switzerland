from datetime import timedelta
import logging
from typing import List, Tuple
from urllib.parse import urlparse

from odoo import SUPERUSER_ID, registry
from odoo.exceptions import AccessDenied
from odoo.http import Controller, Response, request, route
from odoo.tools.config import config

_logger = logging.getLogger(__name__)


AUTH_LOGIN_ROUTE = "/auth/login"
AUTH_REFRESH_ROUTE = "/auth/refresh"
AUTH_LOGOUT_ROUTE = "/auth/logout"


class AuthController(Controller):

    def _validate_fields_as_expected(self, fields: List[str], data: dict) -> None:
        for f in fields:
            if f not in data:
                _logger.info(
                    f"Request failed because field '{f}' was missing from the request data"
                )
                raise AccessDenied
        if len(fields) != len(data):
            _logger.info(f"Unexpected fields provided in request, expected {fields}")
            raise AccessDenied

    def _get_current_hostname(self) -> str:
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        # request.httprequest.url_root.rstrip('/') ??
        return urlparse(base_url).hostname

    @route(
        route=AUTH_LOGIN_ROUTE,
        auth="none",
        type="json",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def login(self):
        self._validate_fields_as_expected(
            ["login", "password", "totp"], request.jsonrequest
        )
        login = request.jsonrequest["login"]
        password = request.jsonrequest["password"]
        totp = request.jsonrequest["totp"]

        db = request.env.cr.dbname
        res_users = registry(db)["res.users"]

        user_id = res_users.authenticate(
            db, login, password, {"totp": totp, "interactive": False}
        )

        user = request.env["res.users"].browse(int(user_id))
        user = user.with_user(user)

        tokens = user.generate_external_auth_token()
        access_token = tokens["access_token"]
        access_token_expires_at = tokens["access_token_expires_at"]
        refresh_token = tokens["refresh_token"]
        # {"user_id": user_id, "auth_tokens": }

        tokens_config = request.env["auth_external.tokens_config"].get_singleton()
        is_cookie_secure = not config.get("debug", False)
        response = Response()

        xmlrpc_path = "/xmlrpc/2/"
        response.set_cookie(
            "access_token",
            access_token,
            expires=access_token_expires_at,
            httponly=True,
            secure=is_cookie_secure,
            domain=self._get_current_hostname(),
            path=xmlrpc_path,
            samesite="Strict"
        )

        # TODO Similar for refresh_token cookie

        return response

    def _validate_refresh_token(self, request) -> Tuple[str, dict]:
        """Validates that the request contains a valid, authentic refresh token.

        Args:
            request (odoo.http.request): The request object

        Raises:
            AccessDenied: if the key "refresh_token" is not in the json data
            AccessDenied: if the refresh_token is None

        Returns:
            dict: Payload of the refresh token, if the token was authentic and non-expired
        """
        self._validate_fields_as_expected(["refresh_token"], request.jsonrequest)

        refresh_token = request.jsonrequest["refresh_token"]

        if refresh_token is None:
            raise AccessDenied

        res_users = request.env["res.users"]
        return refresh_token, res_users._check_refresh_token(refresh_token, None)

    @route(
        route=AUTH_REFRESH_ROUTE,
        auth="none",
        type="json",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def refresh(self):
        refresh_token, payload = self._validate_refresh_token(request)

        # Token passed signature check, so its content is authentic.
        user_id = payload["sub"]

        # sanity check
        if not isinstance(user_id, int):
            _logger.error("Issued a refresh token with an invalid subject.")
            raise AccessDenied

        user = request.env["res.users"].sudo().browse(int(user_id))
        user = user.with_user(user)  # exit sudo

        return user.generate_external_auth_token(refresh_token)

    @route(
        route=AUTH_LOGOUT_ROUTE,
        auth="none",
        type="json",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def logout(self):
        _, payload = self._validate_refresh_token(request)

        # The refresh token is authentic and non-expired but maybe revoked. If
        # it was revoked, that means an attacker might have intercepted this
        # refresh_token and is using it to logout the user. If the refresh token
        # is not revoked, the legitimate user might be trying to logout. In both
        # cases, the token family should be revoked as a fail-safe, so we don't
        # need to check it was revoked.
        refresh_tokens = request.env["auth_external.refresh_tokens"]
        jti = payload["jti"]
        user_id = payload["sub"]
        rt_model = refresh_tokens.sudo().get_by_jti(jti)
        if rt_model is None:
            _logger.warning(
                f"""{user_id=} requested to logout, but the given
                             refresh token ({jti=}) was not found in the
                             database, very strange"""
            )
            raise AccessDenied

        if rt_model.is_revoked:
            _logger.warning(
                f"""[RTRD] Refresh Token Reuse Detection triggered
                             on logout ({jti=}, {user_id=}). Anyway, we were going to revoke
                             the token family, so no harm done (but still
                             worrying: is there an XSS being exploited?) """
            )

        rt_model.sudo().revoke_family()
        return True  # indicates success
