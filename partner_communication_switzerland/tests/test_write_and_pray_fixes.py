##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWriteAndPrayFixes(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sponsor = cls.env["res.partner"].create(
            {
                "firstname": "Johanna",
                "lastname": "Doe",
                "preferred_name": "Jo",
                "title": cls.env.ref("base.res_partner_title_madam").id,
                "lang": "en_US",
            }
        )
        cls.sponsorship_product = cls.env["product.product"].search(
            [("default_code", "=", "sponsorship")], limit=1
        )

    def test_salutation_preferred_name_only_in_write_and_pray(self):
        for lang, expected_name in (
            ("en_US", "Dear {}"),
            ("fr_CH", "{} Doe"),
            ("de_DE", "{}"),
            ("it_IT", "{}"),
        ):
            self.sponsor.lang = lang
            self.sponsor.invalidate_recordset(["salutation"])
            sponsor = self.sponsor
            self.assertTrue(
                sponsor.salutation.endswith(expected_name.format("Johanna")),
                f"{lang}: {sponsor.salutation}",
            )
            wrpr_sponsor = sponsor.with_context(salutation_preferred_name=True)
            self.assertTrue(
                wrpr_sponsor.salutation.endswith(expected_name.format("Jo")),
                f"{lang}: {wrpr_sponsor.salutation}",
            )
        self.sponsor.lang = "fr_CH"
        self.sponsor.invalidate_recordset(["salutation", "informal_salutation"])
        self.assertEqual(
            self.sponsor.with_context(
                salutation_preferred_name=True
            ).informal_salutation,
            "Salut Jo",
        )

    def test_salutation_without_preferred_name(self):
        self.sponsor.preferred_name = False
        self.assertEqual(
            self.sponsor.with_context(salutation_preferred_name=True).salutation,
            "Dear Johanna",
        )

    def test_mobile_warning_needs_a_correspondent(self):
        sponsorship = self.env["recurring.contract"].new({"type": "SWP"})
        self.assertFalse(sponsorship._onchange_write_and_pray_correspondent())

        sponsorship.correspondent_id = self.sponsor
        warning = sponsorship._onchange_write_and_pray_correspondent()
        self.assertIn("mobile", warning["warning"]["message"])

        self.sponsor.mobile = "+41 79 123 45 67"
        self.assertFalse(sponsorship._onchange_write_and_pray_correspondent())

    def _create_sponsorship(self, sponsorship_type="SWP"):
        group = self.env["recurring.contract.group"].create(
            {
                "partner_id": self.sponsor.id,
                "payment_mode_id": self.env.ref(
                    "sponsorship_switzerland.payment_mode_permanent_order"
                ).id,
            }
        )
        return self.env["recurring.contract"].create(
            {
                "type": sponsorship_type,
                "partner_id": self.sponsor.id,
                "correspondent_id": self.sponsor.id,
                "group_id": group.id,
            }
        )

    def test_mobile_entered_on_sponsorship(self):
        sponsorship = self._create_sponsorship()
        sponsorship.correspondent_mobile = "+41 79 123 45 67"
        self.assertEqual(self.sponsor.mobile, "+41 79 123 45 67")

    def test_write_and_pray_contribution_is_invoiced(self):
        self.assertTrue(
            self.sponsorship_product.pricelist_item_count,
            "The test needs a sponsorship product with a fixed price",
        )
        group = self.env["recurring.contract.group"].create(
            {
                "partner_id": self.sponsor.id,
                "payment_mode_id": self.env.ref(
                    "sponsorship_switzerland.payment_mode_permanent_order"
                ).id,
            }
        )
        for sponsorship_type, from_pricelist in (
            ("S", True),
            ("SC", False),
            ("SWP", False),
        ):
            sponsorship = self.env["recurring.contract"].new(
                {
                    "type": sponsorship_type,
                    "group_id": group.id,
                    "contract_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.sponsorship_product.id,
                                "amount": 10,
                                "quantity": 1,
                            },
                        )
                    ],
                }
            )
            line = sponsorship.contract_line_ids
            self.assertEqual(line.amount_from_pricelist, from_pricelist)
            invoice_line = group.build_inv_line_data(contract_line=line)
            if from_pricelist:
                self.assertNotEqual(invoice_line["price_unit"], 10)
            else:
                self.assertEqual(invoice_line["price_unit"], 10, sponsorship_type)

    def test_contribution_amount_sets_quantity(self):
        sponsorship = self.env["recurring.contract"].new({"type": "SWP"})
        line = self.env["recurring.contract.line"].new(
            {
                "contract_id": sponsorship.id,
                "product_id": self.sponsorship_product.id,
                "amount": 0,
                "quantity": 0,
            }
        )
        line.amount = 15
        line._onchange_contribution_amount()
        self.assertEqual(line.quantity, 1)

    def _onboarding_configs(self, sponsorship):
        configs = []

        def send_communication(contract, config, correspondent=True):
            configs.append(config)
            return self.env["partner.communication.job"]

        with patch.object(type(sponsorship), "send_communication", send_communication):
            sponsorship._send_new_dossier()
        return configs

    def test_welcome_by_sms_without_email(self):
        self.sponsor.write(
            {
                "email": False,
                "mobile": "+41 79 123 45 67",
                "global_communication_delivery_preference": "auto_digital",
            }
        )
        sponsorship = self._create_sponsorship()
        self.assertIn(
            self.env.ref("partner_communication_switzerland.config_wrpr_welcome"),
            self._onboarding_configs(sponsorship),
        )

    def test_printed_dossier_without_email_nor_mobile(self):
        self.sponsor.write({"email": False, "mobile": False})
        sponsorship = self._create_sponsorship()
        self.assertEqual(
            self._onboarding_configs(sponsorship),
            [self.env.ref("partner_communication_compassion.planned_dossier")],
        )

    def test_write_and_pray_communications(self):
        job_obj = self.env["partner.communication.job"]
        welcome = self.env.ref("partner_communication_switzerland.config_wrpr_welcome")
        photo = self.env.ref(
            "partner_communication_switzerland.config_onboarding_photo_by_post"
        )
        self.assertTrue(job_obj.new({"config_id": welcome.id})._is_write_and_pray())
        for sponsorship_type, is_wrpr in (("SWP", True), ("S", False)):
            sponsorship = self._create_sponsorship(sponsorship_type)
            job = job_obj.new(
                {"config_id": photo.id, "object_ids": str(sponsorship.id)}
            )
            self.assertEqual(job._is_write_and_pray(), is_wrpr, sponsorship_type)
