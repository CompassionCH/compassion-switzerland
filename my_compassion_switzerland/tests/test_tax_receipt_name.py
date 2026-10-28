##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from datetime import datetime
from unittest.mock import patch

from odoo.tests import TransactionCase, tagged

TAX_RECEIPT = "partner_communication_switzerland.tax_receipt_config"


@tagged("post_install", "-at_install")
class TestTaxReceiptName(TransactionCase):
    """The yearly tax receipt of a donor who gave only an email waits for
    their name: addressed to "(pending)", it is no tax document."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env.ref(TAX_RECEIPT)
        partner_model = cls.env["res.partner"]
        cls.donor = partner_model.create(
            {
                "name": partner_model.MY2_PLACEHOLDER_NAME,
                "email": "tax.receipt.donor@example.org",
                "my2_name_placeholder": True,
                "lang": "en_US",
            }
        )

    def setUp(self):
        super().setUp()

        def pdf(job, data, report_ref):
            """The PDF only states its year and the donor's name."""
            text = f"{data['year']} {job.partner_id.name}"
            return base64.b64encode(text.encode())

        job_class = type(self.env["partner.communication.job"])
        pdf_patch = patch.object(job_class, "_get_pdf_from_data", pdf)
        pdf_patch.start()
        self.addCleanup(pdf_patch.stop)

    def _receipt(self, date):
        """The tax receipt of the donor, made by the yearly generation of date
        (generate_tax_receipts)."""
        return self.env["partner.communication.job"].create(
            {
                "config_id": self.config.id,
                "partner_id": self.donor.id,
                "object_ids": str(self.donor.id),
                "date": date,
            }
        )

    def _pdf_text(self, receipt):
        return base64.b64decode(receipt.attachment_ids.attachment_id.datas).decode()

    def test_the_tax_receipt_waits_for_the_name(self):
        self.assertTrue(self.config.my2_wait_for_name)

    def test_no_receipt_without_a_name(self):
        receipt = self._receipt(datetime(2026, 1, 10))
        receipt.send()
        self.assertEqual(receipt.state, "pending")

    def test_the_named_receipt_keeps_its_year(self):
        """Named a year later, the donor gets the receipt of the year it was
        made for, with their name."""
        receipt = self._receipt(datetime(2025, 1, 10))
        self.assertEqual(self._pdf_text(receipt), f"2024 {self.donor.name}")
        self.donor._my2_replace_placeholder_name("Anna", "Nowak")
        self.assertEqual(len(receipt.attachment_ids), 1)
        self.assertEqual(self._pdf_text(receipt), f"2024 {self.donor.name}")
        self.assertIn("Nowak", self._pdf_text(receipt))
        receipt.send()
        self.assertEqual(receipt.state, "done")

    def test_a_receipt_made_on_new_year_night_is_about_the_past_year(self):
        """Made at 00:30 on 1 January 2027 in Switzerland, still 31 December
        2026 in UTC: the receipt is about 2026."""
        self.env.user.tz = "Europe/Zurich"
        receipt = self._receipt(datetime(2026, 12, 31, 23, 30))
        self.assertEqual(self._pdf_text(receipt), f"2026 {self.donor.name}")
