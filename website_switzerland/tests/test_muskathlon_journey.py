##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import timedelta
from uuid import uuid4

from odoo import fields
from odoo.tests import TransactionCase, tagged

from odoo.addons.base_report_to_printer.models.printing_server import (
    PrintingServer,
)
from odoo.addons.partner_communication_switzerland.tests.common import (
    check_queue_runs,
)


@tagged("post_install", "-at_install")
class TestMuskathlonJourney(TransactionCase):
    """The Muskathlon has the stages of the group visits without the fee and
    the invoice of the trip: activating the account confirms it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        check_queue_runs(cls.env)
        cls.token = uuid4().hex[:8]
        cls.classPatch(
            PrintingServer,
            "_open_connection",
            lambda server, raise_on_error=False: False,
        )

        def ref(xmlid):
            return cls.env.ref(f"muskathlon.{xmlid}")

        cls.stage_unconfirmed = ref("stage_unconfirmed")
        cls.stage_confirmed = ref("stage_fill_profile")
        cls.stage_flights = ref("stage_flights")
        cls.stage_documents = ref("stage_documents")
        cls.stage_criminal_record = ref("stage_criminal_record")
        cls.stage_ready = ref("stage_ready")
        cls.confirmation = ref("registration_confirmation_config")
        cls.passport_and_flight = ref("passport_and_flight_config")
        cls.medical_reminder = ref("medical_reminder_config")
        cls.child_protection = ref("child_protection_config")

        start = fields.Datetime.now() + timedelta(days=200)
        cls.event = cls.env["event.event"].create(
            {
                "name": f"Muskathlon {cls.token}",
                "event_type_id": ref("event_type_muskathlon").id,
                "date_begin": start,
                "date_end": start + timedelta(days=7),
            }
        )
        cls.env["event.mail"].search(
            [("event_id", "!=", cls.event.id), ("mail_done", "=", False)]
        ).mail_done = True

    def test_muskathlon_journey(self):
        partner = self.env["res.partner"].create(
            {
                "name": f"Muskathlete {self.token}",
                "email": f"muskathlete-{self.token}@example.com",
                "lang": "en_US",
            }
        )
        registration = self.env["event.registration"].create(
            {"event_id": self.event.id, "partner_id": partner.id}
        )
        self.assertEqual(registration.stage_id, self.stage_unconfirmed)
        self.assertEqual(registration.state, "draft")

        self.task(registration, "task_activate_account").done = True
        self.assertEqual(
            registration.stage_id,
            self.stage_confirmed,
            "Activating the account should confirm the registration",
        )
        self.assertEqual(registration.state, "open")
        self.assertTrue(self.communications(self.confirmation, partner))
        self.assertEqual(
            registration.stage_id,
            self.stage_confirmed,
            "Confirmed waits for the flights to be set by hand",
        )

        registration.stage_id = self.stage_flights
        self.assertTrue(self.communications(self.passport_and_flight, partner))
        self.task(registration, "task_flight_details").done = True
        self.assertEqual(registration.stage_id, self.stage_documents)
        self.assertTrue(self.communications(self.medical_reminder, partner))
        self.assertFalse(self.communications(self.child_protection, partner))

        registration.task_ids.filtered(
            lambda rel: rel.stage_id == self.stage_documents
        ).done = True
        self.assertEqual(registration.stage_id, self.stage_criminal_record)
        self.assertTrue(self.communications(self.child_protection, partner))

        self.task(registration, "task_criminal").done = True
        self.assertEqual(registration.stage_id, self.stage_ready)

    def task(self, registration, xmlid):
        task = self.env.ref(f"muskathlon.{xmlid}")
        return registration.task_ids.filtered(lambda rel: rel.task_id == task)

    def communications(self, config, partner):
        return self.env["partner.communication.job"].search(
            [("config_id", "=", config.id), ("partner_id", "=", partner.id)]
        )
