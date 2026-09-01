##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestNewDonorOnboarding(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.donor_lastname = "Doe"
        cls.admin = cls.env.ref("base.user_admin")
        cls.admin.tour_enabled = False
        cls.admin.groups_id |= cls.env.ref("account.group_account_invoice")

        cls.env["res.lang"]._activate_lang("fr_CH")
        cls.env["ir.default"].set("res.partner", "lang", "fr_CH")

        cls.first_blog_post = cls.env.ref(
            "partner_communication_switzerland"
            ".config_new_donors_onboarding_1st_blog_post"
        )
        cls.second_blog_post = cls.env.ref(
            "partner_communication_switzerland"
            ".config_new_donors_onboarding_2nd_blog_post"
        )

        cls.env["thankyou.config"].search([]).unlink()
        cls.env["thankyou.config"].create(
            {
                "min_donation_amount": 0,
                "send_mode": "digital",
            }
        )

        cls.donation_product = cls.env["product.product"].create(
            {
                "name": "Donation",
                "type": "service",
                "list_price": 0.0,
                "requires_thankyou": True,
                "partner_communication_config": cls.env.ref(
                    "thankyou_letters.config_thankyou_standard"
                ).id,
            }
        )

    def test_new_donor_onboarding(self):
        self.start_tour("/odoo", "new_donor_onboarding", login="admin")

        donor = self.env["res.partner"].search([("lastname", "=", self.donor_lastname)])
        self.assertEqual(len(donor), 1, "The tour should have created one donor")

        invoice = self.env["account.move"].search(
            [("partner_id", "=", donor.id), ("move_type", "=", "out_invoice")]
        )
        self.assertEqual(len(invoice), 1)
        self.assertEqual(invoice.amount_total, 150)
        self.assertEqual(invoice.payment_state, "paid")

        letter = invoice.communication_id
        self.assertTrue(letter, "No thank you letter was generated for the donation")
        self.assertEqual(letter.partner_id, donor)
        self.assertEqual(letter.get_objects(), invoice.invoice_line_ids)
        # The tour sent it by e-mail from the letter's form
        self.assertEqual(letter.send_mode, "digital")
        self.assertEqual(letter.state, "done")
        self.assertTrue(letter.sent_date)

        email = letter.email_id
        self.assertTrue(email, "Sending the letter produced no e-mail")
        self.assertEqual(email.recipient_ids, donor)
        self.assertEqual(email.state, "sent")
        self.assertIn(donor.firstname, email.body_html)

        # Sending the thank you letter starts the onboarding
        self.assertTrue(
            donor.onboarding_new_donor_start_date,
            "Sending the thank you letter did not start the donor onboarding",
        )
        self.assertTrue(donor.onboarding_new_donor_hash)

        blog_posts = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", donor.id),
                ("config_id", "in", (self.first_blog_post | self.second_blog_post).ids),
            ]
        )
        self.assertEqual(
            blog_posts.config_id,
            self.first_blog_post | self.second_blog_post,
            "The tour should have generated both onboarding blog posts",
        )
