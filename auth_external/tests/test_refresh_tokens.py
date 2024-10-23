import random
import uuid
from odoo.tests.common import TransactionCase
from datetime import datetime, timedelta
class TestRefreshTokens(TransactionCase):

    @staticmethod
    def get_uuid() -> str:
        return str(uuid.uuid4())
    
    def get_refresh_tokens(self):
        return self.env["auth_external.refresh_tokens"]
    
    def create_refresh_token(self):
        exp = datetime.now() + timedelta(hours=1)
        return self.get_refresh_tokens().create({"jti": TestRefreshTokens.get_uuid(), "exp": exp})

    def setUp(self, *args, **kwargs):
        super(TestRefreshTokens, self).setUp(*args, **kwargs)
        self.refresh_token_1 = self.create_refresh_token()

    def test_get_by_jti(self):
        token_1 = self.get_refresh_tokens().get_by_jti(self.refresh_token_1.jti)
        self.assertIsNotNone(token_1)

    def test_revoke_family(self):
        root = self.create_refresh_token()
        rts = [root]
        for _ in range(23):
            old_rt = rts[-1]
            new_rt = self.create_refresh_token()
            old_rt.link_child(new_rt)
            rts.append(new_rt)

        random_rt = random.choice(rts)
        random_rt.revoke_family()

        # Calling revoke_family on any family member should revoke all the members
        for rt in rts:
            self.assertTrue(rt.is_revoked)

