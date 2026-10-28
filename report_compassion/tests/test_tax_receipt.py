##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestTaxReceipt(TransactionCase):
    def _render(self, partner):
        data = {"doc_ids": partner.ids, "year": 2025, "lang": "en_US"}
        html, _ = self.env["ir.actions.report"]._render_qweb_html(
            "report_compassion.tax_receipt_report", partner.ids, data=data
        )
        return html.decode()

    def test_a_donor_without_company_is_signed_by_the_current_company(self):
        """A donor created by the website belongs to no company: the receipt
        is signed as for a donor of the current company."""
        company = self.env.company
        donor = self.env["res.partner"].create(
            {"name": "Anna Nowak", "lang": "en_US", "company_id": False}
        )
        director = company.official_signer_id
        expected = (
            director.user_id.signature_letter
            if director
            else company._get_signature_closing_line()
        )
        self.assertIn(expected, self._render(donor))
