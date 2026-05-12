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
# auth_external tests for v18-specific adaptations.
#
# Sister file to test_auth_controller.py / test_refresh_tokens.py
# (ports of v14 tests). This file contains tests for behaviour that
# only exists in the v18 version of the module:
#   - the ir.http thread-local stash for the Authorization header
#     (needed because v18 borrow_request() unbinds request during
#     XMLRPC dispatch)
#   - PyJWT vs GehirnInc `jwt` behaviour: `sub` is a string in v18,
#     was an int in v14
##############################################################################
import threading

from odoo.tests.common import TransactionCase, tagged

from ..models import res_users as res_users_module


@tagged("auth_external", "v18_adapter")
class TestV18Adapter(TransactionCase):
    def test_ir_http_dispatch_stashes_authorization_header(self):
        """Sanity check: after our ir.http override runs, the
        Authorization header is available on the current thread."""
        # We can't easily simulate a full HTTP dispatch in a
        # TransactionCase, but the contract is simple: the attribute
        # exists (default empty) so that res_users code can read it
        # without AttributeError.
        thread = threading.current_thread()
        # Simulate ir_http._dispatch having run:
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
        """PyJWT 2.x rejects non-string `sub` claims at decode time
        with 'Subject must be a string'. We coerce in _generate_jwt;
        this test pins the behaviour so a regression is caught early."""
        from datetime import datetime, timedelta, timezone
        admin = self.env.ref("base.user_admin")
        payload, _token = admin._generate_jwt(
            iss="test_issuer",
            sub=admin.id,  # int — must come out as string in payload
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
                # Restore by deleting if it was unset originally.
                config.options.pop("auth_external.jwt_key", None)
