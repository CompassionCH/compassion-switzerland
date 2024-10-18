import json
from odoo.tests.common import HttpCase
from ..controllers.auth import AUTH_LOGIN_ROUTE
from http import HTTPStatus
from requests import Response


class TestAuthController(HttpCase):
    TEST_USER_NORMAL = {
        "login": "user_normal",
        "password": "password_normal",
    }
    
    TEST_USER_2FA_CREATE = {
        "login": "user_2fa",
        "password": "password_2fa",
        "totp_secret": "totp_secret",
        "totp_enabled": True
    }

    TEST_USER_2FA = {
        "login": TEST_USER_2FA_CREATE["login"],
        "password": TEST_USER_2FA_CREATE["password"],
        "totp": "123456"
    }

    def setUp(self, *args, **kwargs):
        super(TestAuthController, self).setUp(*args, **kwargs)
        res_users = self.env["res.users"]
        self.test_user_normal = res_users.create(
            TestAuthController.TEST_USER_NORMAL
        )
        self.test_user_2fa = res_users.create(
            TestAuthController.TEST_USER_2FA_CREATE
        )

    def json_post(self, route: str, data: dict) -> Response:
        JSON_HEADERS = {"Content-Type": "application/json"}
        return self.url_open(route, data=json.dumps(data), headers=JSON_HEADERS)

    def assert_access_denied(self, response: Response) -> None:
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response_data = json.loads(response.text)
        self.assertEqual(
            response_data["error"]["data"]["name"], "odoo.exceptions.AccessDenied"
        )

    def should_deny_access(self, login_data: dict) -> None:
        response = self.json_post(AUTH_LOGIN_ROUTE, login_data)
        self.assert_access_denied(response)

    def test_login_should_fail_with_invalid_user(self):
        data = {
            "login": "This username should not exist",
            # and if it does, it's a really weird edge case
            "password": "password",
            "totp": "123456",
        }
        self.should_deny_access(data)

    def test_login_should_succeed_for_normal_user(self):
        response = self.json_post(AUTH_LOGIN_ROUTE, TestAuthController.TEST_USER_NORMAL)
        print(response.text)
        self.assertTrue(False)

    def test_access_denied_incorrect_password(self):
        """
        An attacker is denied access to a normal user account when providing an incorrect password
        """
        data_incorrect_password = TestAuthController.TEST_USER_NORMAL.copy()
        data_incorrect_password["password"] = "incorrect_password"
        self.should_deny_access(data_incorrect_password)

    def test_access_denied_2fa_correct_password_absent_totp(self):
        """
        An attacker is denied access to a 2fa user account when not providing any totp
        """
        data = TestAuthController.TEST_USER_2FA.copy()
        del data["totp"]
        self.should_deny_access(data)

    def test_access_denied_2fa_correct_password_incorrect_totp(self):
        """
        An attacker is denied access to a 2fa user account when providing a correct password but incorrect totp
        """
        data_incorrect_totp = TestAuthController.TEST_USER_2FA.copy()
        data_incorrect_totp["totp"] = "123456" # 1/1'000'000 chance that this is the correct totp and that the test fails
        self.should_deny_access(data_incorrect_totp)

    def test_accses_denied_2fa_incorrect_password_correct_totp(self):
        """
        An attacker is denied access to a 2fa user account when providing an incorrect password but correct totp
        """
        data = TestAuthController.TEST_USER_2FA.copy()
        data["password"] = "incorrect_password"
        data["totp"] = None # TODO

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
