import base64
from datetime import datetime, timedelta
import json
import os
import random
import string
import time

from types import FunctionType
from typing import Any, Tuple, Union
from xmlrpc.client import ServerProxy, Fault

from jwt import AbstractJWKBase

from odoo.addons.auth_totp.models.res_users import TIMESTEP, TOTP_SECRET_SIZE, hotp
from odoo.tests.common import HttpCase
from odoo.tests import tagged
from ..controllers.auth import AUTH_LOGIN_ROUTE, AUTH_REFRESH_ROUTE
from http import HTTPStatus
from requests import Response
from ..models.res_users import issuer_id, user_access_aud, access_token_signing_key, user_refresh_aud, refresh_token_signing_key

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
        secret = self.user_2fa.totp_secret
        key = base64.b32decode(secret)
        totp_int = hotp(key, t)
        return f"{totp_int:06d}"

    def gen_expired_JWT_token(self, user_id: int, JWT_audience: str, signing_key: AbstractJWKBase) -> str:
        res_users = self.env["res.users"]
        one_sec_ago = datetime.now() - timedelta(seconds=1)
        _, token = res_users._generate_jwt(
            issuer_id,
            user_id,
            JWT_audience,
            one_sec_ago,
            signing_key,
        )
        return token

    def gen_expired_JWT_access_token(self, user_id: int) -> str:
        return self.gen_expired_JWT_token(user_id, user_access_aud, access_token_signing_key)
    
    def gen_expired_JWT_refresh_token(self, user_id: int) -> str:
        return self.gen_expired_JWT_token(user_id, user_refresh_aud, refresh_token_signing_key)

    def setUp(self, *args, **kwargs):
        super(TestAuthController, self).setUp(*args, **kwargs)

        test_user = {"name": "Test User"}

        res_users = self.env["res.users"]

        self.user_normal = res_users.create(
            {
                **test_user,
                "login": "user_normal",
                "password": TestAuthController.PASSWORD,
            }
        )
        self.user_2fa = res_users.create(
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

    def assert_xmlrpc_access_denied(self, func: FunctionType, expected_fault_substring: str = "Access Denied") -> None:
        with self.assertRaises(Fault) as cm:
            func()
        self.assertIn(expected_fault_substring, cm.exception.faultString)

    def login(self, login_data: dict, raw_response=False) -> Union[Tuple[str, str, str], Response]:
        resp = self.json_post(AUTH_LOGIN_ROUTE, login_data)
        if raw_response:
            return resp
        data = resp.json()["result"]

        user_id = data["user_id"]

        auth_tokens = data["auth_tokens"]
        access_token = auth_tokens["access_token"]
        refresh_token = auth_tokens["refresh_token"]
        return user_id, access_token, refresh_token
    
    def refresh(self, refresh_token: str, raw_response=False) -> Union[Tuple[str, str, str], Response]:
        """Refresh the tokens using /auth/refresh

        Args:
            refresh_token (str): Refresh token to submit to /auth/refresh

        Returns:
            __Tuple[str, str, str]: access_token, refresh_token, expires_at
        }
        """
        resp = self.json_post(AUTH_REFRESH_ROUTE, {
            "refresh_token": refresh_token
        })
        if raw_response:
            return resp
        data = resp.json()["result"]
        return data["access_token"], data["refresh_token"], data["expires_at"]

    def user_normal_login_data(self) -> dict:
        return {
            "login": self.user_normal.login,
            "password": TestAuthController.PASSWORD,
            "totp": "",
        }

    def user_2fa_login_data(self) -> dict:
        return {
            "login": self.user_2fa.login,
            "password": TestAuthController.PASSWORD,
            "totp": self.get_current_totp(),
        }

    def user_normal_login(self) -> Tuple[int, str, str]:
        """Performs a login for the normal user
    
        Returns:
            __Tuple[int, str, str]: user_id, access_token, refresh_token
        """
        return self.login(self.user_normal_login_data())

    def user_2fa_login(self) -> Tuple[int, str, str]:
        """Performs a login for the 2fa user
    
        Returns:
            __Tuple[int, str, str]: user_id, access_token, refresh_token
        """
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

    def login_should_produce_error(self, login_data: dict, expected_error: str) -> None:
        response = self.login(login_data, raw_response=True)
        self.assert_status_OK(response)
        self.assert_error_name(response, expected_error)

    def assert_error_access_denied(self, resp: Response) -> None:
        self.assert_error_name(resp, "odoo.exceptions.AccessDenied")

    def login_should_deny_access(self, login_data: dict) -> None:
        self.login_should_produce_error(login_data, "odoo.exceptions.AccessDenied")

    def login_should_produce_invalid_totp(self, login_data: dict) -> None:
        self.login_should_produce_error(
            login_data, "odoo.addons.auth_external.models.res_users.InvalidTotp"
        )

    def test_login_should_fail_with_invalid_user(self):
        data = {
            "login": "This username should not exist",
            # and if it does, it's a really weird edge case
            "password": "password",
            "totp": "123456",
        }
        self.login_should_deny_access(data)

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
        self.login_should_deny_access(data_incorrect_password)

    def test_access_denied_2fa_correct_password_absent_totp(self):
        """
        An attacker is denied access to a 2fa user account when not providing any totp
        """
        data = self.user_2fa_login_data()
        del data["totp"]
        self.login_should_produce_error(data, "builtins.KeyError")

    def test_access_denied_2fa_correct_password_incorrect_totp(self):
        """
        An attacker is denied access to a 2fa user account when providing a correct password but incorrect totp
        """
        data_incorrect_totp = self.user_2fa_login_data()
        data_incorrect_totp["totp"] = (
            "123456"  # 1/1'000'000 chance that this is the correct totp and that the test fails
        )
        self.login_should_produce_invalid_totp(data_incorrect_totp)

    def test_access_denied_2fa_incorrect_password_correct_totp(self):
        """
        An attacker is denied access to a 2fa user account when providing an incorrect password but correct totp
        """
        data = self.user_2fa_login_data()
        data["password"] = "incorrect_password"
        self.login_should_deny_access(data)

    def test_no_password_bypass_with_totp_provided(self):
        """
        An attacker is denied access to a normal user account when providing a
        unusual totp
        """
        data = self.user_normal_login_data()
        data["password"] = "incorrect_password"
        data["totp"] = "some very bizarre totp"
        self.login_should_deny_access(data)

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
        self.assert_xmlrpc_access_denied(
            lambda: self.write_user_sig(
                user_id_2fa, access_token_normal, user_id_2fa, "Malicious signature"
            ),
        )

        # incorrect target id
        self.assert_xmlrpc_access_denied(
            lambda: self.write_user_sig(
                user_id_normal, access_token_normal, user_id_2fa, "Malicious signature"
            ),
            "You are not allowed to modify"
        )

    def test_cannot_submit_expired_access_token(self):
        """
        An attacker cannot successfully reuse an expired access_token
        """
        user_id = self.user_normal.id
        exp_access_token = self.gen_expired_JWT_access_token(user_id)
        self.assert_xmlrpc_access_denied(
            lambda: self.write_user_sig(
                user_id, exp_access_token, user_id, "Malicious signature"
            )
        )

    def test_cannot_submit_expired_refresh_token(self):
        """
        An attacker cannot successfully reuse an expired refresh_token
        """
        expired_refresh_token = self.gen_expired_JWT_refresh_token(self.user_normal.id)
        resp = self.refresh(expired_refresh_token, raw_response=True)
        self.assert_error_access_denied(resp)


    def test_can_refresh_access_token_with_valid_refresh_token(self):
        user_id, access_token, refresh_token = self.user_normal_login()
        fresh_access_token, fresh_refresh_token, expires_at = self.refresh(refresh_token)
        # Check fresh access token is indeed fresh
        self.assertNotEqual(access_token, fresh_access_token)
        self.assertNotEqual(refresh_token, fresh_refresh_token) # TODO maybe remove
        rand_sig = self.rand_str(8)
        self.write_user_sig(user_id, fresh_access_token, user_id, rand_sig)
        new_sig = self.read_user_sig(user_id, fresh_access_token, user_id)
        self.assertIn(rand_sig, new_sig)


    def test_cannot_submit_forged_access_token(self):
        """
        An attacker cannot successfully submit an access_token with an invalid signature
        """

    """
    We assume the attacker knows the username of the victim
    TO TEST:
    - 
    - An attacker cannot successfully submit a refresh_token with an invalid signature
    - An attacker cannot successfully reuse an expired refresh token
    """
