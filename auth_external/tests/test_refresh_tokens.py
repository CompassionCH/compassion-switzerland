import random
import uuid
from datetime import datetime, timedelta
from typing import Any

from odoo.tests.common import TransactionCase

from ..models.refresh_tokens import RefreshTokens

FUTURE_TIMEDELTA = timedelta(minutes=3)


class TestRefreshTokens(TransactionCase):
    @staticmethod
    def get_uuid() -> str:
        return str(uuid.uuid4())

    def get_refresh_tokens(self):
        return self.env["auth_external.refresh_tokens"]

    def create_refresh_token(
        self, timediff: timedelta, parent: RefreshTokens = None, user_id=None
    ) -> RefreshTokens:
        exp = datetime.now() + timediff
        user_id = self.test_user.id if user_id is None else user_id
        rt = self.get_refresh_tokens().create(
            {"jti": TestRefreshTokens.get_uuid(), "exp": exp, "user_id": user_id}
        )
        if parent is not None:
            parent.link_child(rt)
        return rt

    def create_user(self) -> Any:
        login = f"testuser_{random.randint(0, 10000)}"
        return self.env["res.users"].create({"name": f"Name {login}", "login": login})

    def setUp(self, *args, **kwargs):
        super().setUp(*args, **kwargs)

        self.test_user = self.create_user()

    def test_get_by_jti(self):
        rt1 = self.create_refresh_token(timedelta(hours=1))
        got_rt1 = self.get_refresh_tokens().get_by_jti(rt1.jti)
        self.assertIsNotNone(got_rt1)
        self.assertEqual(rt1.jti, got_rt1.jti)
        self.assertEqual(rt1.id, got_rt1.id)

    def test_revoke_family(self):
        timediff = timedelta(hours=1)
        root = self.create_refresh_token(timediff)
        rts = [root]
        for _ in range(23):
            old_rt = rts[-1]
            new_rt = self.create_refresh_token(timediff, old_rt)
            rts.append(new_rt)

        random_rt = random.choice(rts)
        random_rt.revoke_family()

        # Calling revoke_family on any family member should revoke all the members
        for rt in rts:
            self.assertTrue(rt.is_revoked)

    def test_remove_expired_tokens(self):
        past_td = timedelta(seconds=-1)
        future_td = timedelta(minutes=1)

        rt1 = self.create_refresh_token(past_td)
        rt2 = self.create_refresh_token(past_td, rt1)
        rt3 = self.create_refresh_token(future_td, rt2)
        rt4 = self.create_refresh_token(future_td, rt3)

        rts = self.get_refresh_tokens().search([])
        self.assertIn(rt1, rts)
        self.assertIn(rt2, rts)
        self.assertIn(rt3, rts)
        self.assertIn(rt4, rts)

        rts.remove_expired_tokens()
        rts = self.get_refresh_tokens().search([])
        # rt1 and rt2 are expired and should have been removed
        self.assertNotIn(rt1, rts)
        self.assertNotIn(rt2, rts)
        # rt3 and rt4 are still valid and should still be present
        self.assertIn(rt3, rts)
        self.assertIn(rt4, rts)

    def test_revoke_tokens_for_user(self):
        test_user_tokens = [
            self.create_refresh_token(FUTURE_TIMEDELTA) for _ in range(42)
        ]

        for i, t in enumerate(test_user_tokens):
            # Revoke some tokens to simulate a realistic scenario
            if i % 3 == 0:
                t.sudo().revoke()

        # function under test
        self.get_refresh_tokens().revoke_tokens_for_user(self.test_user.id)

        for t in test_user_tokens:
            self.assertTrue(t.is_revoked)

    def test_ondelete_cascade(self):
        user = self.create_user()
        tokens = [
            self.create_refresh_token(FUTURE_TIMEDELTA, user_id=user.id)
            for _ in range(13)
        ]

        all_tokens = self.get_refresh_tokens().search([])
        for t in tokens:
            self.assertIn(t, all_tokens)

        user.sudo().unlink()

        all_tokens = self.get_refresh_tokens().search([])
        for t in tokens:
            self.assertNotIn(t, all_tokens)
