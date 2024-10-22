import uuid
from odoo.tests.common import TransactionCase
class TestRefreshTokens(TransactionCase):

    @staticmethod
    def get_uuid() -> str:
        return str(uuid.uuid4())
    
    def get_refresh_tokens(self):
        return self.env["auth_external.refresh_tokens"]

    def setUp(self, *args, **kwargs):
        super(TestRefreshTokens, self).setUp(*args, **kwargs)
        # TODO fix:
        self.refresh_token_1 = self.get_refresh_tokens().create({"jti": TestRefreshTokens.get_uuid()})

    def test_get_by_jti(self):
        token_1 = self.get_refresh_tokens().get_by_jti(self.refresh_token_1.jti)
        self.assertIsNotNone(token_1)