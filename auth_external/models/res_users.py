import json
import logging

import re

import secrets
import contextlib
from datetime import datetime, timedelta

from jwt import JWT, supported_key_types
from jwt.exceptions import JWTDecodeError
from jwt.utils import get_int_from_datetime

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError
from odoo.http import request
from odoo.exceptions import AccessDenied
from odoo.addons.base.models.res_users import Users

_logger = logging.getLogger(__name__)

authorization_extractor = re.compile(r'(\w+)[:=] ?"?(\w+)"?')

# TODO: move those to settings.
global_secret = secrets.token_bytes(256)  # High entropic bytes as secret.
issuer_id = "compassion.ch"
token_duration = 60 * 60 * 5  # Token is only valid for this period of time.
user_auth_grant_aud = "user_auth_grant"


class ExternalAuthUsers(models.Model):
    _inherit = "res.users"

    def make_key(self, secret: bytes):
        return supported_key_types()["oct"](secret)

    def generate_external_auth_token(self):
        """Generates a new JWT token for account authentication for the user.
        :returns: the freshly generated token.
        :raises AccessDenied: if the user can't generate an external auth token.
        """
        self.ensure_one()

        # Can't generate new token if user is authenticated using a token.
        # Require password authentication for token creation.
        if (
            "Authorization" in request.httprequest.headers
            and request.httprequest.headers["Authorization"].startswith("Bearer ")
        ):
            _logger.info(
                "User '%s' tried to refresh their auth token while being authenticated with an auth token."
                % self.login
            )
            raise AccessDenied

        expiration_date = datetime.now() + timedelta(0, token_duration)

        token = JWT().encode(
            {
                # Claims defined in RFC7529#section-4.1
                "iss": issuer_id,
                "sub": self.user_id.id,
                "aud": user_auth_grant_aud,
                "exp": get_int_from_datetime(expiration_date),
                "nbf": get_int_from_datetime(datetime.now()),
                "iat": get_int_from_datetime(datetime.now()),
                "typ": "JWT",
                "jti": "uuid",
            },
            self.make_key(global_secret),
            alg="HS256",
        )

        _logger.info(
            "Generated new auth token for user '%s'. Token expires in %d seconds (%s)"
            % (
                self.login,
                token_duration,
                expiration_date.strftime("%m/%d/%Y, %H:%M:%S"),
            )
        )

        return token

    def _check_external_auth_token(self, token):
        """Verifies the validity of a JWT token for authentication.
        :param token: The token to check for validity.
        :returns: None if the token is valid.
        :raises AccessDenied: if the token is invalid.
        """
        try:
            payload = JWT().decode(token, self.make_key(global_secret), algorithms={"HS256"})
        except JWTDecodeError as exc:
            _logger.info("Auth token check failed '%s'" % exc)
            raise AccessDenied

        if (
            "sub" not in payload
            or payload["sub"] != self.env.user.user_id.id
            or "iss" not in payload
            or payload["iss"] != issuer_id
            or "aud" not in payload
            or payload["aud"] != user_auth_grant_aud
        ):
            raise AccessDenied

    def _check_credentials(self, password, user_agent_env):
        try:
            return super(ExternalAuthUsers, self)._check_credentials(
                password, user_agent_env
            )
        except AccessDenied:
            pass

        if (
            self.env.user.totp_enabled
            and "Authorization" in request.httprequest.headers
        ):
            authorization_header = request.httprequest.headers["Authorization"]

            # Bearer token login attempt.
            if authorization_header.startswith("Bearer "):
                token = authorization_header.split(" ")[1]
                self._check_external_auth_token(token)

                return self.env.user.id

            auth_params = dict(authorization_extractor.findall(authorization_header))

            # Username / password + TOTP login attempt.
            if "totp" in auth_params:
                totp = int(re.sub(r"\s", "", auth_params["totp"]))

                res = Users._check_credentials(self, password, user_agent_env)
                self.env.user._totp_check(totp)

                return res

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
                    # Can't use cache if we are using an Authorization header as token might expire,
                    # and we are not using the password.
                    "Authorization" in request.httprequest.headers
                ):
                    super(ExternalAuthUsers, cls).check.clear_cache(self.env.user)

                return super(ExternalAuthUsers, cls).check(db, uid, passwd)
