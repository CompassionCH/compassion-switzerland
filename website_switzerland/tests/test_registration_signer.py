##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import tagged

from .common import GroupVisitJourneyCase


@tagged("post_install", "-at_install")
class TestRegistrationSigner(GroupVisitJourneyCase):
    """The e-mails of a registration are signed by the event Responsible."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.responsible = cls._internal_user("responsible")
        cls.env["hr.employee"].create(
            {"name": cls.responsible.name, "user_id": cls.responsible.id}
        )
        cls.external = cls._internal_user("external")
        cls.participant = cls.env["res.partner"].create(
            {
                "name": f"Signer participant {cls.token}",
                "email": f"signer-participant-{cls.token}@example.com",
                "lang": "en_US",
            }
        )
        cls.registration = cls.env["event.registration"].create(
            {"event_id": cls.event.id, "partner_id": cls.participant.id}
        )

    @classmethod
    def _internal_user(cls, name):
        return (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": f"Signer {name} {cls.token}",
                    "login": f"signer-{name}-{cls.token}",
                    "email": f"signer-{name}-{cls.token}@example.com",
                    "groups_id": [(6, 0, cls.env.ref("base.group_user").ids)],
                }
            )
        )

    def _send(self):
        return self.registration.send_communication(self.travel_documents.id)

    def test_responsible_signs(self):
        self.event.user_id = self.responsible
        job = self._send()
        self.assertEqual(job.user_id, self.responsible)
        self.assertIn(self.responsible.email, job.body_html)

    def test_non_employee_keeps_rule_signer(self):
        self.event.user_id = self.external
        job = self._send()
        self.assertEqual(job.user_id, self.travel_documents.user_id or self.external)
        self.assertNotIn(self.external.email, job.body_html)
