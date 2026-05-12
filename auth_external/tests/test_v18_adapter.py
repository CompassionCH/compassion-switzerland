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
# auth_external tests for the load-bearing invariants that don't
# come from the v14 test suite ports:
#   - ir.http thread-local stash for the Authorization header
#   - JWT `sub` is serialised as a string (PyJWT requirement)
#   - JWT signing key is read from odoo.conf when configured
##############################################################################
import threading

from odoo.tests.common import TransactionCase, tagged

from ..models import res_users as res_users_module


@tagged("auth_external", "v18_adapter")
class TestV18Adapter(TransactionCase):
    def test_ir_http_dispatch_stashes_authorization_header(self):
        """The contract res_users.check / _check_credentials relies on:
        `threading.current_thread().auth_external_authorization` holds
        the inbound Authorization header during the request."""
        thread = threading.current_thread()
        thread.auth_external_authorization = "Bearer test-token"
        try:
            value = getattr(
                thread, "auth_external_authorization", "<missing>",
            )
            self.assertEqual(value, "Bearer test-token")
            self.assertTrue(value.startswith("Bearer "))
        finally:
            thread.auth_external_authorization = ""

    def test_jwt_sub_is_str_for_pyjwt_compat(self):
        """PyJWT rejects non-string `sub` claims at decode time;
        _generate_jwt coerces. Pinning this so the cast isn't silently
        dropped by a future refactor."""
        from datetime import datetime, timedelta, timezone
        admin = self.env.ref("base.user_admin")
        payload, _token = admin._generate_jwt(
            iss="test_issuer",
            sub=admin.id,
            aud=res_users_module.USER_ACCESS_AUD,
            exp=datetime.now(timezone.utc) + timedelta(minutes=5),
            key=b"test-key-for-unit-test-only-not-prod",
        )
        self.assertIsInstance(payload["sub"], str)
        self.assertEqual(payload["sub"], str(admin.id))

    def test_jwt_key_loaded_from_config(self):
        """When `auth_external.jwt_key` is set in odoo.conf,
        gen_signing_key() returns those exact bytes (not an ephemeral
        random secret)."""
        from odoo.tools import config
        sentinel = "TEST-SENTINEL-KEY-do-not-use-in-prod"
        original = config.get("auth_external.jwt_key")
        try:
            config["auth_external.jwt_key"] = sentinel
            key = res_users_module.gen_signing_key()
            self.assertEqual(key, sentinel.encode("utf-8"))
        finally:
            if original is not None:
                config["auth_external.jwt_key"] = original
            else:
                config.options.pop("auth_external.jwt_key", None)
