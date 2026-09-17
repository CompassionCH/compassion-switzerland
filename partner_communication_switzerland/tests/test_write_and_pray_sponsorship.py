##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests import HttpCase, tagged

from .common import (
    check_queue_runs,
    enable_connect_fake,
    get_or_create_origin,
    get_sponsorable_child,
    setup_tour_admin,
)

SPONSOR_FIRSTNAME = "Jane"
SPONSOR_LASTNAME = "Doe"
SPONSOR_EMAIL = "Jane.doe@example.org"
SPONSOR_MOBILE = "079 123 45 67"
CHILD_LOCAL_ID = "TR087654321"
ORIGIN_NAME = "Write and Pray Tour"


def setup_tour_data(env):
    setup_tour_admin(env)
    return {
        "origin": get_or_create_origin(env, ORIGIN_NAME),
        "child": get_sponsorable_child(env, CHILD_LOCAL_ID),
        "sponsor": _setup_sponsor(env),
    }


def _setup_sponsor(env):
    partners = env["res.partner"].search([("email", "=", SPONSOR_EMAIL)])
    if len(partners) > 1:
        raise ValueError(
            f"{len(partners)} partners share the e-mail {SPONSOR_EMAIL}. The "
            "tour would not know which one to pick: please merge them or give "
            "the sponsor of the tour an address of their own."
        )
    vals = {
        "firstname": SPONSOR_FIRSTNAME,
        "lastname": SPONSOR_LASTNAME,
        "email": SPONSOR_EMAIL,
        "mobile": SPONSOR_MOBILE,
        "birthdate_date": fields.Date.today() - relativedelta(years=20),
        "street": "Rue Galilée 3",
        "zip": "1400",
        "city": "Yerdon-les-Bains",
        "country_id": env.ref("base.ch").id,
        "lang": "en_US",
        "global_communication_delivery_preference": "sms",
    }
    if partners:
        sponsor = partners
        sponsor.write(vals)
        env["partner.communication.job"].search(
            [("partner_id", "=", sponsor.id)]
        ).unlink()
    else:
        sponsor = env["res.partner"].create(vals)

    groups = env["recurring.contract.group"].search([("partner_id", "=", sponsor.id)])
    if len(groups) != 1:
        groups.unlink()
        env["recurring.contract.group"].create(
            {
                "partner_id": sponsor.id,
                "payment_mode_id": env.ref(
                    "sponsorship_switzerland.payment_mode_permanent_order"
                ).id,
            }
        )
    return sponsor


@tagged("post_install", "-at_install")
class TestWriteAndPraySponsorship(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        check_queue_runs(cls.env)

        enable_connect_fake(cls)

        tour_data = setup_tour_data(cls.env)
        cls.origin = tour_data["origin"]
        cls.child = tour_data["child"]
        cls.sponsor = tour_data["sponsor"]

        cls.wrpr_welcome_config = cls.env.ref(
            "partner_communication_switzerland.config_wrpr_welcome"
        )
        cls.photo_config = cls.env.ref(
            "partner_communication_switzerland.config_onboarding_photo_by_post"
        )

    def test_write_and_pray_sponsorship(self):
        self.start_tour("/odoo", "write_and_pray_sponsorship", login="admin")

        sponsorship = self.env["recurring.contract"].search(
            [("child_id", "=", self.child.id)]
        )
        self.assertEqual(
            len(sponsorship), 1, "The tour should have created one sponsorship"
        )
        self.assertEqual(sponsorship.type, "SWP")
        self.assertEqual(sponsorship.correspondent_id, self.sponsor)
        self.assertEqual(sponsorship.partner_id, self.sponsor)
        self.assertEqual(sponsorship.origin_id, self.origin)

        self.assertEqual(
            sponsorship.total_amount,
            0,
            "A Write&Pray sponsorship should not cost anything",
        )
        self.assertTrue(
            sponsorship.contract_line_ids,
            "A Write&Pray sponsorship needs its contract lines, "
            "otherwise it does not show up on the sponsor's profile",
        )

        self.assertEqual(sponsorship.state, "active")
        self.assertTrue(sponsorship.start_date, "The sponsorship has no start date")
        self.assertTrue(
            sponsorship.activation_date, "The sponsorship has no activation date"
        )

        self.assertFalse(
            any(sponsorship.invoice_line_ids.mapped("price_subtotal")),
            "A Write&Pray sponsorship should not be charged to the sponsor",
        )

        onboarding_configs = self.wrpr_welcome_config | self.photo_config
        communications = self.env["partner.communication.job"].search(
            [
                ("partner_id", "=", self.sponsor.id),
                ("config_id", "in", onboarding_configs.ids),
            ]
        )
        self.assertEqual(
            communications.config_id,
            onboarding_configs,
            "The onboarding of the Write&Pray sponsor generated the wrong "
            "communications",
        )
        self.assertEqual(
            set(communications.mapped("state")),
            {"pending"},
            "The onboarding communications should be ready to be sent",
        )
        welcome = communications.filtered(
            lambda job: job.config_id == self.wrpr_welcome_config
        )
        self.assertEqual(
            welcome.send_mode,
            "sms",
            "The Write&Pray welcome is sent by SMS",
        )
