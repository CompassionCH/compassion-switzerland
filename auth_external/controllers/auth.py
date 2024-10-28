from datetime import timedelta
import json
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

    def _validate_and_parse_fields_as_expected(self, fields: List[str]) -> dict:
        data = json.loads(request.httprequest.data)
        for f in fields:
            if f not in data:
                _logger.info(
                    f"Request failed because field '{f}' was missing from the request data"
                )
                raise AccessDenied
        if len(fields) != len(data):
            _logger.info(f"Unexpected fields provided in request, expected {fields}")
            raise AccessDenied
        
        return data

    def _get_current_hostname(self) -> str:
        if config.get("debug", False):
            # ValueError: Setting 'domain' for a cookie on a server running
            # locally (ex: localhost) is not supported by complying browsers.
            # You should have something like: '127.0.0.1 localhost
            # dev.localhost' on your hosts file and then point your server to
            # run on 'dev.localhost' and also set 'domain' for 'dev.localhost'
            return "dev.localhost" 
        base_url = request.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return urlparse(base_url).hostname
    
    def _make_resp_with_tokens(self, tokens: dict, user_id: int) -> Response:
        """Build a response which sets the access and refresh tokens as cookies.

        Args:
            tokens (dict): Dict containing the access and refresh tokens and their expiration dates, produced by generate_external_auth_token

        Returns:
            Response: built response containing the cookies.
        """
        access_token = tokens["access_token"]
        access_token_expires_at = tokens["access_token_expires_at"]
        refresh_token = tokens["refresh_token"]
        refresh_token_expires_at = tokens["refresh_token_expires_at"]

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
        response.set_cookie(
            "refresh_token",
            refresh_token,
            expires=refresh_token_expires_at,
            httponly=True,
            secure=is_cookie_secure,
            domain=self._get_current_hostname(),
            path=AUTH_REFRESH_ROUTE,
            samesite="Strict"
        )
        response.set_data(json.dumps({
            "access_token_expires_at": access_token_expires_at.isoformat(),
            "user_id": user_id
        }))
        return response

    @route(
        route=AUTH_LOGIN_ROUTE,
        auth="none",
        type="http",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def login(self):
        data = self._validate_and_parse_fields_as_expected(
            ["login", "password", "totp"]
        )

        login = data["login"]
        password = data["password"]
        totp = data["totp"]

        db = request.env.cr.dbname
        res_users = registry(db)["res.users"]

        user_id = res_users.authenticate(
            db, login, password, {"totp": totp, "interactive": False}
        )

        user = request.env["res.users"].browse(int(user_id))
        user = user.with_user(user)

        tokens = user.generate_external_auth_token()
        response = self._make_resp_with_tokens(tokens, user_id)
        return response

    def _validate_refresh_token(self) -> Tuple[str, dict]:
        """Validates that the request contains a valid, authentic refresh token.

        Raises:
            AccessDenied: if the key "refresh_token" is not in the json data
            AccessDenied: if the refresh_token is None

        Returns:
            Tuple[str, dict]: Raw refresh token and refresh token payload (if authentic and valid)
        """
        if len(request.httprequest.data) != 0:
            raise AccessDenied("A refresh/logout request should not contain any data")

        if "refresh_token" not in request.httprequest.cookies:
            raise AccessDenied("A refresh/logout request should contain a refresh_token in the cookies")

        refresh_token = request.httprequest.cookies["refresh_token"]

        if refresh_token is None:
            raise AccessDenied

        res_users = request.env["res.users"]
        refresh_token_payload = res_users._check_refresh_token(refresh_token, None)
        return refresh_token, refresh_token_payload

    @route(
        route=AUTH_REFRESH_ROUTE,
        auth="none",
        type="http",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def refresh(self):
        refresh_token, payload = self._validate_refresh_token()

        # Token passed signature check, so its content is authentic.
        user_id = payload["sub"]

        # sanity check
        if not isinstance(user_id, int):
            _logger.error("Issued a refresh token with an invalid subject.")
            raise AccessDenied

        user = request.env["res.users"].sudo().browse(int(user_id))
        user = user.with_user(user)  # exit sudo

        tokens = user.generate_external_auth_token(refresh_token)
        resp = self._make_resp_with_tokens(tokens, user_id)
        return resp

    @route(
        route=AUTH_LOGOUT_ROUTE,
        auth="none",
        type="http",
        methods=["GET"],
        csrf=False,
        cors="*",
    )
    def logout(self):
        _, payload = self._validate_refresh_token()

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
        return "Logout successful."  # indicates success
