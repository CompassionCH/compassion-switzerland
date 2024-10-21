import logging

from odoo import SUPERUSER_ID, registry
from odoo.exceptions import AccessDenied
from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)



AUTH_LOGIN_ROUTE = "/auth/login"
AUTH_REFRESH_ROUTE = "/auth/refresh"
class AuthController(Controller):

    @route(
        route=AUTH_LOGIN_ROUTE,
        auth="none",
        type="json",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def login(self):
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

        return {"user_id": user_id, "auth_tokens": user.generate_external_auth_token()}

    @route(
        route=AUTH_REFRESH_ROUTE,
        auth="none",
        type="json",
        methods=["POST"],
        csrf=False,
        cors="*",
    )
    def refresh(self):
        if "refresh_token" not in request.jsonrequest:
            raise AccessDenied

        refresh_token = request.jsonrequest["refresh_token"]

        if refresh_token is None:
            raise AccessDenied

        db = request.env.cr.dbname
        res_users = registry(db)["res.users"]

        payload = res_users._check_refresh_token(refresh_token, None)

        # Token passed signature check, so its content is authentic.
        user_id = payload["sub"]

        # sanity check
        if not isinstance(user_id, int):
            _logger.error("Issued a refresh token with an invalid subject.")
            raise AccessDenied

        user = request.env["res.users"].with_user(SUPERUSER_ID).browse(int(user_id))
        user = user.with_user(user)

        return user.generate_external_auth_token(refresh_token)
