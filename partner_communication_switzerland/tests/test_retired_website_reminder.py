##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import importlib.util
from pathlib import Path

from odoo.tests import TransactionCase, tagged

MODULE = "partner_communication_switzerland"
MIGRATION = (
    Path(__file__).parents[1] / "migrations" / "18.0.1.1.19" / "post-migration.py"
)


def _migration():
    spec = importlib.util.spec_from_file_location("t3644_migration", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@tagged("post_install", "-at_install")
class TestRetiredWebsiteReminder(TransactionCase):
    """The v14 website sponsorship confirmation and reminder e-mails link to a
    MyCompassion 1.0 page that no longer exists: nothing sends them anymore."""

    def test_reminder_automation_removed(self):
        for name in ("sms_sponsorship_reminder", "sms_sponsorship_reminder_action"):
            with self.subTest(name=name):
                self.assertFalse(
                    self.env.ref(f"{MODULE}.{name}", raise_if_not_found=False)
                )

    def test_configs_and_templates_archived(self):
        # Absent on a new database, archived on an upgraded one.
        for name in (
            "sms_registration_confirmation_1",
            "sms_registration_reminder",
            "sms_confirmation_email_1",
            "sms_reminder_email",
        ):
            with self.subTest(name=name):
                record = self.env.ref(f"{MODULE}.{name}", raise_if_not_found=False)
                self.assertFalse(record and record.active)

    def test_unsent_reminders_cancelled(self):
        """Reminders waiting to go out at the upgrade are not sent, the sent
        ones stay as they are."""
        config = self.env.ref("partner_communication.default_communication")
        partner = self.env["res.partner"].create(
            {"name": "T3644 Sponsor", "email": "t3644@example.org"}
        )
        Job = self.env["partner.communication.job"]
        pending, processing, done = (
            Job.create({"partner_id": partner.id, "config_id": config.id})
            for __ in range(3)
        )
        processing.state = "processing"
        done.state = "done"
        task = self.env["queue.job"].create(
            {
                "uuid": "t3644-queued-reminder",
                "state": "pending",
                "model_name": Job._name,
                "method_name": "_send_mail_asynchronous",
                "records": processing,
                "args": (),
                "kwargs": {},
                "identity_key": f"{Job._name}._send_mail.{processing.id}",
            }
        )

        _migration().cancel_unsent(self.env, config)

        self.assertEqual(pending.state, "cancel")
        self.assertEqual(processing.state, "cancel")
        self.assertEqual(task.state, "cancelled")
        self.assertEqual(done.state, "done")
