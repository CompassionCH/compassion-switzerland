##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import TransactionCase, tagged

MODULE = "partner_communication_switzerland"


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
