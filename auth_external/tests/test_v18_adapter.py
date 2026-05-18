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
    def test_ir_http_dispatch_stashes_and_clears_authorization_header(self):
        """`_dispatch` must (a) stash the inbound Authorization header on
        the current thread before calling the endpoint and (b) clear it
        on return, otherwise a worker thread leaks the header from one
        request to the next."""
        from unittest.mock import MagicMock, patch

        from ..models import ir_http as ir_http_module

        captured = {}

        def fake_endpoint(*args, **kwargs):
            captured["mid_dispatch"] = getattr(
                threading.current_thread(),
                "auth_external_authorization",
                None,
            )
            return "ok"

        fake_request = MagicMock()
        fake_request.httprequest.environ = {
            "HTTP_AUTHORIZATION": "Bearer test-token",
        }

        IrHttp = self.env["ir.http"]
        auth_ext_def_cls = ir_http_module.IrHttp
        mro = type(IrHttp).__mro__
        auth_idx = mro.index(auth_ext_def_cls)
        parent_with_dispatch = next(
            c for c in mro[auth_idx + 1 :] if "_dispatch" in c.__dict__
        )

        with (
            patch.object(ir_http_module, "request", fake_request),
            patch.object(
                parent_with_dispatch,
                "_dispatch",
                classmethod(lambda cls, endpoint: endpoint()),
            ),
        ):
            type(IrHttp)._dispatch(fake_endpoint)

        self.assertEqual(captured["mid_dispatch"], "Bearer test-token")
        self.assertEqual(
            getattr(
                threading.current_thread(),
                "auth_external_authorization",
                None,
            ),
            "",
            "Authorization header must be cleared after dispatch returns",
        )

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
