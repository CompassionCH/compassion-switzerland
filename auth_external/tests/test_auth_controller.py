import base64
import json
import os
import random
import string
import time

from typing import Any, Tuple
from xmlrpc.client import ServerProxy, Fault

from odoo.addons.auth_totp.models.res_users import TIMESTEP, TOTP_SECRET_SIZE, hotp
from odoo.tests.common import HttpCase
from odoo.tests import tagged
from ..controllers.auth import AUTH_LOGIN_ROUTE
from http import HTTPStatus
from requests import Response

TEST_DB_NAME = "t1486"
NO_PASSWORD = "None"


@tagged("post_install", "-at_install")
class TestAuthController(HttpCase):

    PASSWORD = "password"

    @staticmethod
    def gen_totp_secret() -> str:
        secret_bytes_count = TOTP_SECRET_SIZE // 8
        secret = base64.b32encode(os.urandom(secret_bytes_count)).decode()
        return secret

    def get_current_totp(self) -> str:
        t = int(time.time() / TIMESTEP)
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
        response = self.login(login_data, raw_response=True)
        self.assert_status_OK(response)
        result = response.json()["result"]
        self.assertIn("user_id", result)
        self.assertIn("auth_tokens", result)
        auth_tokens = result["auth_tokens"]
        self.assertIn("access_token", auth_tokens)
        self.assertNotEqual(auth_tokens["access_token"], "")

    def login(self, login_data: dict, raw_response=False) -> Any:
        resp = self.json_post(AUTH_LOGIN_ROUTE, login_data)
        if raw_response:
            return resp
        data = resp.json()["result"]

        user_id = data["user_id"]

        auth_tokens = data["auth_tokens"]
        access_token = auth_tokens["access_token"]
        refresh_token = auth_tokens["refresh_token"]
        return user_id, access_token, refresh_token

    def user_normal_login_data(self) -> dict:
        return {
            "login": self.test_user_normal.login,
            "password": TestAuthController.PASSWORD,
            "totp": "",
        }

    def user_2fa_login_data(self) -> dict:
        return {
            "login": self.test_user_2fa.login,
            "password": TestAuthController.PASSWORD,
            "totp": self.get_current_totp(),
        }

    def user_normal_login(self) -> Tuple[int, str, str]:
        return self.login(self.user_normal_login_data())

    def user_2fa_login(self) -> Tuple[int, str, str]:
        return self.login(self.user_2fa_login_data())

    def xmlrpc_execute_kw(
        self,
        user_id: int,
        access_token: str,
        model_name: str,
        method: str,
        pos_args: list,
        kw_args={},
    ) -> dict:
        models = ServerProxy(
            f"{self.xmlrpc_url}object",
            headers=[("Authorization", f"Bearer {access_token}")],
        )
        return models.execute_kw(
            TEST_DB_NAME, user_id, NO_PASSWORD, model_name, method, pos_args, kw_args
        )

    def read_user_sig(
        self, request_user_id: int, access_token: str, target_user_id: int
    ) -> dict:
        res = self.xmlrpc_execute_kw(
            request_user_id,
            access_token,
            "res.users",
            "read",
            [[target_user_id]],
            {"fields": ["signature"]},
        )
        return res[0]["signature"]

    def write_user_sig(
        self,
        request_user_id: int,
        access_token: str,
        target_user_id: int,
        new_signature: str,
    ) -> dict:
        self.xmlrpc_execute_kw(
            request_user_id,
            access_token,
            "res.users",
            "write",
            [[target_user_id], {"signature": new_signature}],
        )

    def should_produce_error(self, login_data: dict, expected_error: str) -> None:
        response = self.login(login_data, raw_response=True)
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
        self.should_deny_access(data)

    def test_no_password_bypass_with_totp_provided(self):
        """
        An attacker is denied access to a normal user account when providing a
        unusual totp
        """
        data = self.user_normal_login_data()
        data["password"] = "incorrect_password"
        data["totp"] = "some very bizarre totp"
        self.should_deny_access(data)

    def rand_str(self, length: int):
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(length))

    def test_fresh_access_token_is_accepted(self):
        """
        A normal user can make rpc calls with a valid access token
        """
        user_id, access_token, _ = self.user_normal_login()
        rand_sig = self.rand_str(8)
        self.write_user_sig(user_id, access_token, user_id, rand_sig)
        new_sig = self.read_user_sig(user_id, access_token, user_id)
        self.assertIn(rand_sig, new_sig)

    def test_access_denied_without_correct_user_id(self):
        """
        An attacker cannot use their access_token to modify data from another account
        """
        user_id_normal, access_token_normal, _ = self.user_normal_login()
        user_id_2fa, _, _ = self.user_2fa_login()
        # The attacker (normal user) tries to modify the signature of the victim (2fa user)
        # incorrect requester id and target id
        self.assertRaises(
            Fault,
            lambda: self.write_user_sig(
                user_id_2fa, access_token_normal, user_id_2fa, "Malicious signature"
            ),
        )

        # incorrect target id
        self.assertRaises(
            Fault,
            lambda: self.write_user_sig(
                user_id_normal, access_token_normal, user_id_2fa, "Malicious signature"
            ),
        )

    

    

    """
    We assume the attacker knows the username of the victim
    TO TEST:
    - An attacker cannot successfully submit a forged access token
    - An attacker cannot successfully submit a forged refresh token
    - An attacker cannot successfully reuse an expired access token
    - An attacker cannot successfully reuse an expired refresh token
    """
