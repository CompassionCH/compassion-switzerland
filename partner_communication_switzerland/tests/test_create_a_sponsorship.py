##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import io
import logging
from unittest import mock
from uuid import uuid4

from dateutil.relativedelta import relativedelta
from PIL import Image

from odoo import fields
from odoo.tests import HttpCase, tagged
from odoo.tools.config import config

_logger = logging.getLogger(__name__)

SPONSOR_LASTNAME = "Doe"
SPONSOR_EMAIL = "marie.doe@example.org"
CHILD_LOCAL_ID = "TR098765432"
ORIGIN_NAME = "Sponsorship Creation Tour"


def setup_tour_data(env):
    admin = env.ref("base.user_admin")
    admin.tour_enabled = False
    admin.groups_id |= env.ref("account.group_account_invoice")
    # The tour looks for its records by the name they have in English.
    admin.lang = "en_US"

    # The tour sends both of these to GMC itself, from the Message Center.
    actions = env.ref("sponsorship_compassion.upsert_partner") | env.ref(
        "sponsorship_compassion.create_sponsorship"
    )
    actions.auto_process = False

    origin = env["recurring.contract.origin"].search(
        [("type", "=", "other"), ("other_name", "=", ORIGIN_NAME)], limit=1
    )
    if not origin:
        origin = env["recurring.contract.origin"].create(
            {"type": "other", "other_name": ORIGIN_NAME}
        )

    child = env["compassion.child"].search([("local_id", "=", CHILD_LOCAL_ID)], limit=1)
    if not child:
        child = _create_consigned_child(env)
    elif child.state != "N":
        # A run of the tour sponsors the child, which takes them off the
        # market. Release them so that the tour can pick them again.
        reset_tour_data(env, child)
    return {"origin": origin, "child": child}


def reset_tour_data(env, child=None):
    """Puts back what a previous run of the tour consumed."""
    if child is None:
        child = env["compassion.child"].search(
            [("local_id", "=", CHILD_LOCAL_ID)], limit=1
        )
    if not child:
        return
    sponsorships = env["recurring.contract"].search([("child_id", "in", child.ids)])
    _logger.info(
        "Releasing %s from %s sponsorship(s)", CHILD_LOCAL_ID, len(sponsorships)
    )
    sponsorships.with_context(force_delete=True).unlink()
    child.invalidate_recordset()
    if not child.hold_id:
        child.hold_id = _create_hold(env, "No Money Hold", child)
    if child.state != "N":
        child.child_unsponsored()
        child.invalidate_recordset()
    if child.state != "N":
        raise ValueError(
            f"The child {CHILD_LOCAL_ID} is still in state {child.state} and "
            "cannot be sponsored again by the tour."
        )


def _create_hold(env, hold_type, child=None):
    """A hold of the given type, valid for long enough to run the tour."""
    return env["compassion.hold"].create(
        {
            "hold_id": uuid4().hex,
            "type": hold_type,
            "expiration_date": fields.Datetime.now() + relativedelta(weeks=2),
            "primary_owner": env.user.id,
            "child_id": child.id if child else False,
        }
    )


def _create_consigned_child(env):
    """A child on a consignment hold, ready to be sponsored."""
    hold = _create_hold(env, "Consignment Hold")
    child = (
        env["compassion.child"]
        .with_context(no_upsert=True)
        .create(
            {
                "local_id": CHILD_LOCAL_ID,
                "global_id": uuid4().hex,
                "firstname": "Aylin",
                "preferred_name": "Aylin",
                "lastname": "Yilmaz",
                "state": "N",
                "birthdate": fields.Date.today() - relativedelta(years=8),
                "project_id": _create_project(env).id,
                "hold_id": hold.id,
            }
        )
    )
    hold.child_id = child
    _add_child_pictures(child)
    return child


def _create_project(env):
    """Creates the project the child of the tour belongs to."""
    icp_details = env.ref("child_compassion.icp_details")
    auto_process = icp_details.auto_process
    icp_details.auto_process = False
    try:
        return env["compassion.project"].create(
            {"fcp_id": CHILD_LOCAL_ID[:5], "name": "Onboarding Tour Project"}
        )
    finally:
        icp_details.auto_process = auto_process


def _add_child_pictures(child):
    env = child.env
    picture = io.BytesIO()
    Image.new("RGB", (16, 16), "white").save(picture, "PNG")
    with mock.patch(
        "odoo.addons.child_compassion.models.child_pictures.urlopen",
        side_effect=lambda *args, **kwargs: io.BytesIO(picture.getvalue()),
    ):
        pictures = env["compassion.child.pictures"].create(
            {
                "child_id": child.id,
                "image_url": "https://media.ci.org/image/upload/v1/tour.jpg",
            }
        )
    if not pictures.fullshot:
        raise ValueError("The child of the tour needs a portrait")


@tagged("post_install", "-at_install")
class TestCreateASponsorship(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The tour drains queue.job.replacement itself instead of waiting for
        # the cron. with_delay_sh queues on queue.job when the OCA module is
        # installed, and the tour would then silently run nothing.
        assert "queue.job" not in cls.env, "The tour needs queue_job to be uninstalled"

        cls.startClassPatcher(mock.patch.dict(config.options, {"connect_fake": True}))

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
