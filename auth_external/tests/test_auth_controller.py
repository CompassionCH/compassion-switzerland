import base64
import json
import os
import time
from odoo.addons.auth_totp.models.res_users import TOTP_SECRET_SIZE, hotp
from odoo.tests.common import HttpCase
from odoo.tests import tagged
from ..controllers.auth import AUTH_LOGIN_ROUTE
from http import HTTPStatus
from requests import Response


@tagged("post_install", "-at_install")
class TestAuthController(HttpCase):

    PASSWORD = "password"

    @staticmethod
    def gen_totp_secret() -> str:
        secret_bytes_count = TOTP_SECRET_SIZE // 8
        secret = base64.b32encode(os.urandom(secret_bytes_count)).decode()
        return secret

    def get_current_totp(self) -> str:
        t = int(time.time())
        secret = self.test_user_2fa.totp_secret
        key = base64.b32decode(secret)
        totp_int = hotp(key, t)
        return f"{totp_int:06d}"

    def setUp(self, *args, **kwargs):
        super(TestAuthController, self).setUp(*args, **kwargs)

        test_user = {"name": "Test User"}

        res_users = self.env["res.users"]

        self.test_user_normal = res_users.create(
            {
                **test_user,
                "login": "user_normal",
                "password": TestAuthController.PASSWORD,
            }
        )
        self.test_user_2fa = res_users.create(
            {
                **test_user,
                "login": "user_2fa",
                "password": TestAuthController.PASSWORD,
                "totp_secret": TestAuthController.gen_totp_secret(),
                "totp_enabled": True,
            }
        )

    def json_post(self, route: str, data: dict) -> Response:
        JSON_HEADERS = {"Content-Type": "application/json"}
        return self.url_open(route, data=json.dumps(data), headers=JSON_HEADERS)

    def assert_status_OK(self, response) -> None:
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def assert_error_name(self, response: Response, expected_error: str) -> None:
        self.assertEqual(response.json()["error"]["data"]["name"], expected_error)

    def assert_login_success(self, login_data: dict) -> None:
        response = self.login(login_data)
        self.assert_status_OK(response)
        result = response.json()["result"]
        self.assertIn("user_id", result)
        self.assertIn("auth_tokens", result)
        auth_tokens = result["auth_tokens"]
        self.assertIn("access_token", auth_tokens)
        self.assertNotEqual(auth_tokens["access_token"], "")

    def login(self, login_data: dict) -> Response:
        return self.json_post(AUTH_LOGIN_ROUTE, login_data)
    
    def user_normal_login_data(self) -> dict:
        return {
            "login": self.test_user_normal.login,
            "password": TestAuthController.PASSWORD,
            "totp": ""
        }
    
    def user_2fa_login_data(self) -> dict:
        return {
            "login": self.test_user_2fa.login,
            "password": TestAuthController.PASSWORD,
            "totp": self.get_current_totp()
        }
    

    def should_produce_error(self, login_data: dict, expected_error: str) -> None:
        response = self.login(login_data)
        self.assert_status_OK(response)
        self.assert_error_name(response, expected_error)

    def should_deny_access(self, login_data: dict) -> None:
        self.should_produce_error(login_data, "odoo.exceptions.AccessDenied")

    def should_produce_invalid_totp(self, login_data: dict) -> None:
        self.should_produce_error(
            login_data, "odoo.addons.auth_external.models.res_users.InvalidTotp"
        )

    def test_login_should_fail_with_invalid_user(self):
        data = {
            "login": "This username should not exist",
            # and if it does, it's a really weird edge case
            "password": "password",
            "totp": "123456",
        }
        self.should_deny_access(data)

    def test_login_should_succeed_for_normal_user(self):
        self.assert_login_success(self.user_normal_login_data())

    def test_login_should_succeed_for_2fa_user(self):
        self.assert_login_success(self.user_2fa_login_data())

    def test_access_denied_incorrect_password(self):
        """
        An attacker is denied access to a normal user account when providing an incorrect password
        """
        data_incorrect_password = self.user_normal_login_data()
        data_incorrect_password["password"] = "incorrect_password"
        self.should_deny_access(data_incorrect_password)

    def test_access_denied_2fa_correct_password_absent_totp(self):
        """
        An attacker is denied access to a 2fa user account when not providing any totp
        """
        data = self.user_2fa_login_data()
        del data["totp"]
        self.should_produce_error(data, "builtins.KeyError")

    def test_access_denied_2fa_correct_password_incorrect_totp(self):
        """
        An attacker is denied access to a 2fa user account when providing a correct password but incorrect totp
        """
        data_incorrect_totp = self.user_2fa_login_data()
        data_incorrect_totp["totp"] = (
            "123456"  # 1/1'000'000 chance that this is the correct totp and that the test fails
        )
        self.should_produce_invalid_totp(data_incorrect_totp)

    def test_access_denied_2fa_incorrect_password_correct_totp(self):
        """
        An attacker is denied access to a 2fa user account when providing an incorrect password but correct totp
        """
        data = self.user_2fa_login_data()
        data["password"] = "incorrect_password"
        data["totp"] = None  # TODO

    """
    We assume the attacker knows the username of the victim
    TO TEST:
    - 
    - 
    - 
    - An attacker is denied access to a normal user account when providing a totp
    - An attacker cannot successfully submit a forged access token
    - An attacker cannot successfully submit a forged refresh token
    - An attacker cannot successfully reuse an expired access token
    - An attacker cannot successfully reuse an expired refresh token
    """
