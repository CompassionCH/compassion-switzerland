##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestEventRegistrationSetup(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Keep in sync with the tour.
        cls.registration_fee = 250
        cls.admin = cls.env.ref("base.user_admin")
        cls.admin.tour_enabled = False
        # The tour looks for menus, buttons and stages by their English name.
        cls.admin.lang = "en_US"

        cls.event_type = cls.env.ref("website_switzerland.event_type_group_visit")
        cls.registration_product = cls.env.ref("event_product.product_product_event")

    def test_event_registration_setup(self):
        events_before = self.env["crm.event.compassion"].search([])

        # The default 60s are not enough when the frontend assets of the
        # website still have to be built.
        self.start_tour("/odoo", "event_registration_setup", login="admin", timeout=180)

        event = self.env["crm.event.compassion"].search([]) - events_before
        self.assertEqual(len(event), 1, "The tour should have created one event")
        self.assertEqual(event.event_type_id, self.event_type)
        self.assertGreater(
            event.start_date,
            fields.Datetime.now(),
            "The tour should have planned the event in the future",
        )
        self.assertGreater(event.end_date, event.start_date)

        odoo_event = event.odoo_event_id
        self.assertTrue(
            odoo_event, "Opening the registrations did not create an Odoo event"
        )
        self.assertEqual(odoo_event.event_type_id, self.event_type)
        self.assertEqual(odoo_event.date_begin, event.start_date)
        self.assertEqual(odoo_event.date_end, event.end_date)
        self.assertEqual(
            odoo_event.stage_id,
            self.env.ref("event.event_stage_announced"),
            "The tour should have announced the registrations",
        )
        # The seats limit comes from the registration template, otherwise the
        # event would be fully booked before anyone registers.
        self.assertEqual(odoo_event.seats_max, self.event_type.seats_max)
        self.assertFalse(odoo_event.registration_full)
        self.assertTrue(odoo_event.registration_open)

        ticket = odoo_event.event_ticket_ids
        self.assertEqual(len(ticket), 1, "The event should have one registration fee")
        self.assertEqual(ticket.product_id, self.registration_product)
        self.assertEqual(ticket.price, self.registration_fee)

        # The mail schedulers of the registration template are communication
        # rules, which have no mail template to point at.
        self.assertEqual(
            odoo_event.event_mail_ids.mapped("communication_id"),
            self.event_type.event_type_mail_ids.mapped("communication_id"),
            "The communication rules of the registration template were not copied",
        )
