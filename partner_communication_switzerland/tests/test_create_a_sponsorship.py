##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.tests import HttpCase, tagged

from .common import (
    check_queue_runs,
    enable_connect_fake,
    get_or_create_origin,
    get_sponsorable_child,
    setup_tour_admin,
)

SPONSOR_LASTNAME = "Doe"
SPONSOR_EMAIL = "marie.doe@example.org"
CHILD_LOCAL_ID = "TR098765432"
ORIGIN_NAME = "Sponsorship Creation Tour"


def setup_tour_data(env):
    """Entry point of the fixture, also called by the reset_tour.py script."""
    setup_tour_admin(env)
    return {
        "origin": get_or_create_origin(env, ORIGIN_NAME),
        "child": get_sponsorable_child(env, CHILD_LOCAL_ID),
    }


@tagged("post_install", "-at_install")
class TestCreateASponsorship(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        check_queue_runs(cls.env)

        enable_connect_fake(cls)

        tour_data = setup_tour_data(cls.env)
        cls.origin = tour_data["origin"]
        cls.child = tour_data["child"]

        cls.welcome_config = cls.env.ref(
            "partner_communication_switzerland"
            ".config_onboarding_sponsorship_confirmation"
        )
        cls.photo_config = cls.env.ref(
            "partner_communication_switzerland.config_onboarding_photo_by_post"
        )
        cls.upsert_partner = cls.env.ref("sponsorship_compassion.upsert_partner")
        cls.upsert_sponsorship = cls.env.ref(
            "sponsorship_compassion.create_sponsorship"
        )
        cls.permanent_order = cls.env.ref(
            "sponsorship_switzerland.payment_mode_permanent_order"
        )
        cls.sponsor_category = cls.env.ref(
            "partner_compassion.res_partner_category_sponsor"
        )

    def test_create_a_sponsorship(self):
        self.start_tour("/odoo", "create_a_sponsorship", login="admin")

        sponsorship = self.env["recurring.contract"].search(
            [("child_id", "=", self.child.id)]
        )
        self.assertEqual(
            len(sponsorship), 1, "The tour should have created one sponsorship"
        )
        sponsor = sponsorship.correspondent_id
        self.assertEqual(sponsor.lastname, SPONSOR_LASTNAME)
        self.assertEqual(sponsor.email, SPONSOR_EMAIL)
        self.assertEqual(sponsorship.partner_id, sponsor)
        self.assertEqual(sponsorship.payment_mode_id, self.permanent_order)
        self.assertEqual(sponsorship.origin_id, self.origin)

        # Paying the first invoice activated the sponsorship
        self.assertEqual(sponsorship.state, "active")
        self.assertTrue(sponsorship.start_date, "The sponsorship has no start date")
        self.assertTrue(
            sponsorship.activation_date, "The sponsorship has no activation date"
        )
        self.assertIn(
            self.sponsor_category,
            sponsor.category_id,
            "The sponsor did not get the Sponsor tag",
        )

        invoices = sponsorship.invoice_line_ids.move_id
        self.assertTrue(invoices, "No invoice was generated for the sponsorship")
        self.assertTrue(
            all(invoice.invoice_date.day == 1 for invoice in invoices),
            "The sponsorship invoices should be issued on the 1st of the month",
        )
        self.assertIn(
            "paid",
            invoices.mapped("payment_state"),
            "The tour should have paid the first invoice of the sponsorship",
        )

        onboarding_configs = self.welcome_config | self.photo_config
        communications = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", sponsor.id),
                ("config_id", "in", onboarding_configs.ids),
            ]
        )
        self.assertEqual(
            communications.config_id,
            onboarding_configs,
            "The onboarding of the new sponsor generated the wrong communications",
        )
        self.assertEqual(
            set(communications.mapped("state")),
            {"pending"},
            "The onboarding communications should be ready to be sent",
        )

        messages = self.env["gmc.message"].search([("partner_id", "=", sponsor.id)])
        partner_message = messages.filtered(
            lambda m: m.action_id == self.upsert_partner
        )
        commitment_message = messages.filtered(
            lambda m: m.action_id == self.upsert_sponsorship
        )
        self.assertTrue(partner_message, "The sponsor was not declared to GMC")
        self.assertEqual(partner_message.mapped("state"), ["success"])
        self.assertTrue(sponsor.global_id, "The sponsor got no global ID from GMC")

        self.assertTrue(commitment_message, "The commitment was not declared to GMC")
        self.assertEqual(commitment_message.mapped("state"), ["success"])
        self.assertTrue(
            sponsorship.gmc_commitment_id,
            "The sponsorship got no global ID from GMC",
        )
