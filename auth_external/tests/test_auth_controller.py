import base64
from datetime import datetime, timedelta
import json
import os
import random
import string
import time

from typing import Callable, Tuple, Union
from xmlrpc.client import ServerProxy, Fault

from jwt import AbstractJWKBase

from odoo.addons.auth_totp.models.res_users import TIMESTEP, TOTP_SECRET_SIZE, hotp
from odoo.tests.common import HttpCase
from odoo.tests import tagged
from ..controllers.auth import AUTH_LOGIN_ROUTE, AUTH_LOGOUT_ROUTE, AUTH_REFRESH_ROUTE
from http import HTTPStatus
from requests import Response
from ..models.res_users import (
    gen_signing_key,
    USER_ACCESS_AUD,
    access_token_signing_key,
    USER_REFRESH_AUD,
    refresh_token_signing_key,
)

TEST_DB_NAME = "t1486"
NO_PASSWORD = "None"
ACCESS_DENIED_XMLRPC = "Access Denied"

@tagged("post_install", "-at_install")
class TestAuthController(HttpCase):

    PASSWORD = "password"

    @staticmethod
    def rand_str(length: int):
        letters = string.ascii_lowercase
        return "".join(random.choice(letters) for _ in range(length))

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

    def gen_timedelta_JWT(
        self,
        user_id: int,
        JWT_audience: str,
        signing_key: AbstractJWKBase,
        delta: timedelta,
    ) -> str:
        res_users = self.env["res.users"]
        one_sec_ago = datetime.now() + delta
        _, token = res_users._generate_jwt(
            self.tokens_config.issuer_id,
            user_id,
            JWT_audience,
            one_sec_ago,
            signing_key,
        )
        return token

    def gen_expired_JWT(
        self, user_id: int, JWT_audience: str, signing_key: AbstractJWKBase
    ) -> str:
        delta = timedelta(
            seconds=-1
        )  # generated token expired 1 second in the past (expired)
        return self.gen_timedelta_JWT(user_id, JWT_audience, signing_key, delta)

    def gen_short_duration_JWT(
        self, user_id: int, JWT_audience: str, signing_key: AbstractJWKBase
    ) -> str:
        delta = timedelta(
            seconds=5
        )  # generated token expires 5 seconds in the future (valid)
        return self.gen_timedelta_JWT(user_id, JWT_audience, signing_key, delta)

    def gen_expired_JWT_access_token(self, user_id: int) -> str:
        return self.gen_expired_JWT(user_id, USER_ACCESS_AUD, access_token_signing_key)

    def gen_expired_JWT_refresh_token(self, user_id: int) -> str:
        return self.gen_expired_JWT(
            user_id, USER_REFRESH_AUD, refresh_token_signing_key
        )

    def gen_forged_JWT(self, user_id: int, JWT_audience: str) -> str:
        forging_key = gen_signing_key()
        return self.gen_timedelta_JWT(
            user_id, JWT_audience, forging_key, timedelta(seconds=5)
        )

    def gen_forged_JWT_access_token(self, user_id: int) -> str:
        return self.gen_forged_JWT(user_id, USER_ACCESS_AUD)

    def gen_forged_JWT_refresh_token(self, user_id: int) -> str:
        return self.gen_forged_JWT(user_id, USER_REFRESH_AUD)

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
        
        self.tokens_config = self.env["auth_external.tokens_config"].sudo().get_singleton()

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

    def assert_xmlrpc_access_denied(
        self, func: Callable, expected_fault_substring: str = ACCESS_DENIED_XMLRPC
    ) -> None:
        with self.assertRaises(Fault) as cm:
            func()
        self.assertIn(expected_fault_substring, cm.exception.faultString)

    def assert_can_write_user_data(self, user_id: int, access_token: str) -> None:
        rand_sig = TestAuthController.rand_str(8)
        self.write_user_sig(user_id, access_token, user_id, rand_sig)
        new_sig = self.read_user_sig(user_id, access_token, user_id)
        self.assertIn(rand_sig, new_sig)

    def assert_cannot_write_user_data(
        self,
        user_id: int,
        access_token: str,
        target_user_id=None,
        expected_fault_substring=None,
    ) -> None:
        write_fn = lambda: self.write_user_sig(
            user_id,
            access_token,
            user_id if target_user_id is None else target_user_id,
            "Malicious signature",
        )
        if expected_fault_substring is None:
            self.assert_xmlrpc_access_denied(write_fn)
        else:
            self.assert_xmlrpc_access_denied(write_fn, expected_fault_substring)

    def assert_refresh_access_denied(self, refresh_token: str) -> None:
        resp = self.refresh(refresh_token, raw_response=True)
        self.assert_error_access_denied(resp)

    def login(
        self, login_data: dict, raw_response=False
    ) -> Union[Tuple[str, str, str], Response]:
        resp = self.json_post(AUTH_LOGIN_ROUTE, login_data)
        if raw_response:
            return resp
        data = resp.json()["result"]

        user_id = data["user_id"]

        auth_tokens = data["auth_tokens"]
        access_token = auth_tokens["access_token"]
        refresh_token = auth_tokens["refresh_token"]
        return user_id, access_token, refresh_token

    def refresh(
        self, refresh_token: str, raw_response=False
    ) -> Union[Tuple[str, str, str], Response]:
        """Refresh the tokens using /auth/refresh

        Args:
            refresh_token (str): Refresh token to submit to /auth/refresh

        Returns:
            __Tuple[str, str, str]: access_token, refresh_token, expires_at
        }
        """
        resp = self.json_post(AUTH_REFRESH_ROUTE, {"refresh_token": refresh_token})
        if raw_response:
            return resp
        data = resp.json()["result"]
        return data["access_token"], data["refresh_token"], data["expires_at"]
    
    def logout(self, refresh_token: str, raw_response = False) -> Response:
        resp = self.json_post(AUTH_LOGOUT_ROUTE, {"refresh_token": refresh_token})
        if raw_response:
            return resp
        return resp.json()["result"]


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

    def test_access_denied_with_additional_fields(self):
        self.login_should_deny_access({
            **self.user_normal_login_data(),
            "some_malicious_field": "some value"
        })

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
        self.login_should_deny_access(data)

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

    def test_fresh_access_token_is_accepted(self):
        """
        A normal user can make rpc calls with a valid access token
        """
        user_id, access_token, _ = self.user_normal_login()
        self.assert_can_write_user_data(user_id, access_token)

    def test_access_denied_without_correct_user_id(self):
        """
        An attacker cannot use their access_token to modify data from another account
        """
        user_id_normal, access_token_normal, _ = self.user_normal_login()
        user_id_2fa, _, _ = self.user_2fa_login()
        # The attacker (normal user) tries to modify the signature of the victim (2fa user)
        # incorrect requester id and target id
        self.assert_cannot_write_user_data(
            user_id_2fa, access_token_normal, user_id_2fa
        )

        # incorrect target id
        self.assert_cannot_write_user_data(
            user_id_normal,
            access_token_normal,
            user_id_2fa,
            "You are not allowed to modify",
        )

    def test_can_submit_short_lived_access_token(self):
        """
        A legitimate user can submit an access token which will soon expire
        """
        user_id = self.user_normal.id
        access_token = self.gen_short_duration_JWT(
            user_id, USER_ACCESS_AUD, access_token_signing_key
        )
        self.assert_can_write_user_data(user_id, access_token)

    def test_cannot_submit_expired_access_token(self):
        """
        An attacker cannot successfully reuse an expired access_token
        """
        user_id = self.user_normal.id
        exp_access_token = self.gen_expired_JWT_access_token(user_id)
        self.assert_cannot_write_user_data(user_id, exp_access_token)

    def test_cannot_submit_expired_refresh_token(self):
        """
        An attacker cannot successfully reuse an expired refresh_token
        """
        expired_refresh_token = self.gen_expired_JWT_refresh_token(self.user_normal.id)
        resp = self.refresh(expired_refresh_token, raw_response=True)
        self.assert_error_access_denied(resp)

    def test_can_refresh_access_token_with_valid_refresh_token(self):
        """
        A legitimate user can use their refresh_token to get a valid fresh access_token
        """
        user_id, access_token, refresh_token = self.user_normal_login()
        fresh_access_token, fresh_refresh_token, expires_at = self.refresh(
            refresh_token
        )
        # Check fresh access token is indeed fresh
        self.assertNotEqual(access_token, fresh_access_token)
        self.assertNotEqual(refresh_token, fresh_refresh_token)
        self.assert_can_write_user_data(user_id, fresh_access_token)

    def test_cannot_submit_forged_access_token(self):
        """
        An attacker cannot successfully submit an access_token with an invalid signature
        """
        user_id = self.user_normal.id
        forged_access_token = self.gen_forged_JWT_access_token(user_id)
        self.assert_cannot_write_user_data(user_id, forged_access_token)

    def test_cannot_submit_forged_refresh_token(self):
        """
        An attacker cannot successfully submit a refresh_token with an invalid signature
        """
        user_id = self.user_normal.id
        forged_refresh_token = self.gen_forged_JWT_refresh_token(user_id)
        resp = self.refresh(forged_refresh_token, raw_response=True)
        self.assert_error_access_denied(resp)

    def get_refresh_tokens(self):
        return self.env["auth_external.refresh_tokens"]

    def test_refresh_token_reuse_detection_mechanism_works(self):
        """
        An attacker cannot reuse a previously used refresh token. If they try,
        they trigger the refresh token reuse detection mechanism and all tokens
        of the family are revoked.
        """
        _, _, rt1 = self.user_normal_login()

        rts = [rt1]
        for _ in range(9):
            # perform a few correct refreshes
            _, new_rt, _  = self.refresh(rts[-1])
            rts.append(new_rt)

        _, last_rt, _ = self.refresh(rts[-1])

        # Oh no, an attacker intercepted a random refresh token (but no the last one which is still valid)
        rt_intercepted = random.choice(rts)
        # They try to use it to get fresh tokens.
        # Haha, it doesn't work! Automatic reuse detection was triggered!
        self.assert_refresh_access_denied(rt_intercepted)

        # Automatic reuse detection also revoked the last rt (which was still valid before)
        self.assert_refresh_access_denied(last_rt)
        
    
    def test_refresh_token_revoked_after_logout(self):
        """
        An attacker cannot reuse a refresh token after it was used to logout.
        """
        user_id, at, rt = self.user_normal_login()
        logout_resp = self.logout(rt)
        self.assertTrue(logout_resp)
        self.assert_refresh_access_denied(rt)

    def test_cannot_logout_with_expired_refresh_token(self):
        """
        An attacker cannot logout with an expired refresh token
        """
        expired_rt = self.gen_expired_JWT_refresh_token(self.user_normal.id)
        self.assert_error_access_denied(self.logout(expired_rt, raw_response=True))

    def test_full_2fa_user_lifecycle(self):
        # First, they login
        uid, at1, rt1 = self.user_2fa_login()

        # Then, they make a few requests to protected resources
        for _ in range(5):
            self.assert_can_write_user_data(uid, at1)

        # Then, they refresh their tokens
        at2, rt2, exp2 = self.refresh(rt1)

        # They make a few other requests
        for _ in range(7):
            self.assert_can_write_user_data(uid, at2)

        # Finally, they logout
        self.assertTrue(self.logout(rt2))

        


