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
        child = self.create_refresh_token()
        root.link_child(child)
        grandchild = self.create_refresh_token()
        child.link_child(grandchild)

        child.revoke_family()

        self.assertTrue(root.is_revoked)
        self.assertTrue(child.is_revoked)
        self.assertTrue(grandchild.is_revoked)

