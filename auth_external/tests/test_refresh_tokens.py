import random
import uuid
from odoo.tests.common import TransactionCase
from datetime import datetime, timedelta
from ..models.refresh_tokens import RefreshTokens
class TestRefreshTokens(TransactionCase):

    @staticmethod
    def get_uuid() -> str:
        return str(uuid.uuid4())
    
    def get_refresh_tokens(self):
        return self.env["auth_external.refresh_tokens"]
    
    def create_refresh_token(self, timediff: timedelta, parent: RefreshTokens = None) -> RefreshTokens:
        exp = datetime.now() + timediff
        rt = self.get_refresh_tokens().create({"jti": TestRefreshTokens.get_uuid(), "exp": exp})
        if parent is not None:
            parent.link_child(rt)
        return rt

    def setUp(self, *args, **kwargs):
        super(TestRefreshTokens, self).setUp(*args, **kwargs)

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
        future_td = timedelta(hours=1)

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



