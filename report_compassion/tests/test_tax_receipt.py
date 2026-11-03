##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

from ..wizards import print_tax_receipt


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


@tagged("post_install", "-at_install")
class TestTaxReceiptLanguage(TransactionCase):
    """T3627: a receipt is in the language of its donor when someone prints it
    from the backend, and in the language of the website on MyCompassion."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for lang in ("de_DE", "fr_CH"):
            cls.env["res.lang"]._activate_lang(lang)
        cls.german = cls.env["res.partner"].create(
            {"name": "Anna Keller", "lang": "de_DE"}
        )
        cls.french = cls.env["res.partner"].create(
            {"name": "Marie Dubois", "lang": "fr_CH"}
        )

    def _wizard(self, partners, **context):
        return (
            self.env["print.tax_receipt"]
            .with_context(lang="en_US", active_ids=partners.ids, **context)
            .create({"year": 2025})
        )

    def _download(self, wizard):
        # Reports are HTML in tests: join them instead of merging PDFs
        with patch(f"{print_tax_receipt.__name__}.merge_pdf", b"".join):
            wizard.get_report()
        return base64.b64decode(wizard.pdf_download).decode()

    def test_backend_print_is_in_the_donor_language(self):
        action = self._wizard(self.german).get_report()
        self.assertEqual(action["data"]["lang"], "de_DE")
        self.assertEqual(action["context"]["lang"], "de_DE")

    def test_several_donors_each_get_their_language(self):
        wizard = self._wizard(self.german + self.french)
        html = self._download(wizard)
        self.assertEqual(wizard.state, "pdf")
        self.assertIn("Spenden", html)
        self.assertIn("Vos dons", html)
        self.assertNotIn("Your donations", html)

    def test_mycompassion_uses_the_website_language(self):
        wizard = self._wizard(self.german, tax_receipt_lang="fr_CH")
        wizard.pdf = True
        html = self._download(wizard)
        self.assertIn("Vos dons", html)
        self.assertNotIn("Spenden", html)
        self.assertTrue(wizard.pdf_name.endswith("_2025.pdf"))
