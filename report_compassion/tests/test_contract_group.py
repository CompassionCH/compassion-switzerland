##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

QR_IBAN = "CH93 3000 0999 9999 9999 9"


@tagged("post_install", "-at_install")
class TestCompanyQrrAccount(TransactionCase):
    """The payment slips print the QR-IBAN bank account of the company."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.groups = cls.env["recurring.contract.group"]
        cls.company_without_account = cls.env["res.company"].create(
            {"name": "AAA Company Without Bank Account", "sequence": 0}
        )
        cls.env.user.company_ids |= cls.company_without_account

    def _create_qr_account(self, company):
        account = self.env["res.partner.bank"].create(
            {"acc_number": QR_IBAN, "partner_id": company.partner_id.id}
        )
        self.assertTrue(
            account.l10n_ch_qr_iban, f"{QR_IBAN} should be read as a QR-IBAN"
        )
        return account

    def test_qrr_account__of_the_company_of_the_group(self):
        company = self.env["res.company"].create({"name": "QR-IBAN Company"})
        account = self._create_qr_account(company)
        partner = self.env["res.partner"].create(
            {"name": "QR-IBAN Sponsor", "company_id": False}
        )
        group = self.groups.create({"partner_id": partner.id, "company_id": company.id})

        self.assertEqual(
            group.get_company_qrr_account(),
            account,
            "The payment slip should use the bank account of its own company",
        )

    def test_qrr_account__falls_back_on_a_company_that_has_one(self):
        self._create_qr_account(self.env.company)

        found = self.groups.with_company(
            self.company_without_account
        ).get_company_qrr_account()

        self.assertTrue(
            found.l10n_ch_qr_iban,
            "A company without a QR-IBAN should not shadow the ones that have "
            "one, the payment slips have no account to print otherwise",
        )

    def test_qrr_account__without_any_qr_iban(self):
        self.env["res.partner.bank"].search(
            [("l10n_ch_qr_iban", "!=", False)]
        ).l10n_ch_qr_iban = False

        with self.assertRaises(UserError):
            self.groups.get_company_qrr_account()
