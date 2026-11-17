##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from unittest import mock

from odoo.tests import TransactionCase, tagged

from .common import create_consigned_child


@tagged("post_install", "-at_install")
class TestStandingOrderPl(TransactionCase):
    """Polish sponsors get the details of the standing order to set up in
    their bank, not a Swiss payment slip."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env["res.company"].create(
            {
                "name": "Fundacja Compassion Polska Test",
                "country_id": cls.env.ref("base.pl").id,
                "currency_id": cls.env.ref("base.PLN").id,
                "vat": "9542914362",
                "street": "ul. Warszawska 40/2A",
                "zip": "40-008",
                "city": "Katowice",
                "email": "kontakt@example.pl",
            }
        )
        bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "PL16 1050 1214 1000 0090 8755 1132",
                "partner_id": cls.company.partner_id.id,
            }
        )
        journal = cls.env["account.journal"].create(
            {
                "name": "ING Test",
                "code": "INGT",
                "type": "bank",
                "company_id": cls.company.id,
                "bank_account_id": bank.id,
            }
        )
        cls.standing_order = cls.env["account.payment.mode"].create(
            {
                "name": "Standing Order Test",
                "company_id": cls.company.id,
                "payment_method_id": cls.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "bank_account_link": "fixed",
                "fixed_journal_id": journal.id,
            }
        )
        cls.sponsor = cls.env["res.partner"].create(
            {
                "name": "Jan Kowalski",
                "lang": "en_US",
                "country_id": cls.env.ref("base.pl").id,
            }
        )
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=[cls.company.id])
        )
        cls.group = cls.env["recurring.contract.group"].create(
            {
                "partner_id": cls.sponsor.id,
                "payment_mode_id": cls.standing_order.id,
                "ref": "2033880 - 359095",
            }
        )
        # The hold is not sent to GMC Connect.
        update_hold = mock.patch(
            "odoo.addons.child_compassion.models.compassion_hold"
            ".CompassionHold.update_hold"
        )
        update_hold.start()
        cls.addClassCleanup(update_hold.stop)
        cls.child = create_consigned_child(cls.env, "KE999900001")
        cls.sponsorship = (
            cls.env["recurring.contract"]
            .with_company(cls.company)
            .create(
                {
                    "company_id": cls.company.id,
                    "child_id": cls.child.id,
                    "partner_id": cls.sponsor.id,
                    "correspondent_id": cls.sponsor.id,
                    "group_id": cls.group.id,
                    "type": "S",
                    "contract_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": cls.env["product.product"]
                                .search([], limit=1)
                                .id,
                                "amount": 150.0,
                                "quantity": 1,
                            },
                        )
                    ],
                }
            )
        )

    def setUp(self):
        super().setUp()
        # A new record keeps its values in the cache, which every test clears.
        self.job = self.env["partner.communication.job"].new(
            {"partner_id": self.sponsor.id}
        )

    def test_values(self):
        values = self.job._get_standing_order_pl_values(self.sponsorship)
        self.assertEqual(values["account"], "16 1050 1214 1000 0090 8755 1132")
        self.assertEqual(values["amount"], 150.0)
        self.assertEqual(values["reference"], "2033880 - 359095")
        self.assertEqual(values["children"], self.child)
        self.assertTrue(base64.b64decode(values["qr_code"]).startswith(b"\x89PNG"))

    def test_reference_falls_back_to_the_sponsorship(self):
        for ref in (False, "/"):
            self.group.ref = ref
            values = self.job._get_standing_order_pl_values(self.sponsorship)
            self.assertEqual(values["reference"], self.sponsorship.reference)

    def test_zbp_qr_value(self):
        value = self.job._get_zbp_qr_value(
            self.company, "16105012141000009087551132", 150.0, "2033880 - 359095"
        )
        self.assertEqual(
            value,
            "9542914362|PL|16105012141000009087551132|015000"
            "|Fundacja Compassion|2033880 - 359095|||",
        )

    def test_zbp_qr_value_limits(self):
        value = self.job._get_zbp_qr_value(
            self.company, "16105012141000009087551132", 12000.0, "x" * 40
        )
        fields_values = value.split("|")
        self.assertEqual(len(fields_values), 9)
        # Above 9999.99 the payer types the amount.
        self.assertEqual(fields_values[3], "000000")
        self.assertEqual(len(fields_values[5]), 32)

    def test_attachment(self):
        attachments = self.job._get_standing_order_pl_attachments(self.sponsorship)
        self.assertEqual(len(attachments), 1)
        report_name, pdf = next(iter(attachments.values()))
        self.assertEqual(
            report_name, "partner_communication_switzerland.standing_order_pl"
        )
        # Tests render the report in HTML.
        content = base64.b64decode(pdf).decode()
        self.assertIn("16 1050 1214 1000 0090 8755 1132", content)
        self.assertIn("2033880 - 359095", content)
        self.assertIn("KE999900001", content)
        self.assertIn("data:image/png;base64,", content)

    def test_card_sponsorship_gets_no_standing_order(self):
        if "payment_provider_id" not in self.standing_order._fields:
            self.skipTest("my_compassion gives payment modes a provider")
        provider = self.env["payment.provider"].create(
            {"name": "PayU Test", "code": "none", "company_id": self.company.id}
        )
        self.standing_order.payment_provider_id = provider
        self.assertEqual(
            self.job._get_standing_order_pl_attachments(self.sponsorship), {}
        )

    def test_slip_function_routes_polish_sponsorships(self):
        # As contract_waiting leaves it, without its GMC messages.
        self.sponsorship.write({"state": "waiting", "sds_state": "active"})
        attachments = self.job.get_sponsorship_payment_slip_attachments()
        self.assertEqual(
            [v[0] for v in attachments.values()],
            ["partner_communication_switzerland.standing_order_pl"],
        )

    def test_email_sentence(self):
        sentence = self.sponsorship.get_payment_type_attachment_string()
        self.assertIn("standing order", sentence)
        self.assertIn("150", sentence)
        self.assertNotIn("CHF", sentence)

    def test_email_sentence_card(self):
        if "payment_provider_id" not in self.standing_order._fields:
            self.skipTest("my_compassion gives payment modes a provider")
        self.standing_order.payment_provider_id = self.env["payment.provider"].create(
            {"name": "PayU Test", "code": "none", "company_id": self.company.id}
        )
        sentence = self.sponsorship.get_payment_type_attachment_string()
        self.assertIn("charged to your card", sentence)

    def test_email_sentence_added_to_existing_order(self):
        """A second sponsorship in the group of an active one: the sponsor
        increases their standing order to the total of the attached details."""
        self.sponsorship.write({"state": "active", "sds_state": "active"})
        second = self.sponsorship.copy(
            {
                "child_id": create_consigned_child(self.env, "KE999900002").id,
                "group_id": self.group.id,
            }
        )
        second.write({"state": "waiting", "sds_state": "active"})
        self.assertEqual(second.total_amount, 150.0)
        sentence = second.get_payment_type_attachment_string()
        self.assertIn("increase your existing standing order", sentence)
        self.assertIn("150", sentence)
        self.assertIn("300", sentence)
        # The attached details give the same total.
        values = self.job._get_standing_order_pl_values(self.sponsorship | second)
        self.assertEqual(values["amount"], 300.0)

    def test_polish_salutation(self):
        sponsor = self.sponsor.with_context(lang="pl_PL")
        sponsor.lang = "pl_PL"
        self.assertEqual(sponsor.salutation, "Dzień dobry, Jan")
        sponsor.title = self.env.ref("partner_compassion.res_partner_title_family")
        # The salutation is computed without dependencies.
        sponsor.invalidate_recordset(["salutation"])
        self.assertEqual(sponsor.salutation, "Droga Rodzino")

    def test_sent_from_the_polish_company(self):
        job = self.env["partner.communication.job"].create(
            {
                "partner_id": self.sponsor.id,
                "config_id": self.env.ref(
                    "partner_communication_switzerland"
                    ".config_onboarding_sponsorship_confirmation"
                ).id,
                "object_ids": str(self.sponsorship.id),
            }
        )
        self.assertEqual(job.company_id, self.company)
        self.assertIn("kontakt@example.pl", job.email_from)
        self.assertEqual(job.reply_to, "kontakt@example.pl")
