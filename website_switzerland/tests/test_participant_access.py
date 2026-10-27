##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import json
from types import SimpleNamespace

from odoo import http
from odoo.exceptions import AccessError
from odoo.tests import tagged

from .common import GroupVisitJourneyCase

PASSPORT = b"%PDF-1.4 passport of the owner"
FORGED = b"%PDF-1.4 forged document"


@tagged("post_install", "-at_install")
class TestParticipantAccess(GroupVisitJourneyCase):
    """T3572: the documents, flights and comments of a participant are theirs
    and the staff's only, whatever the visitor sends."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.owner, cls.owner_login = cls._portal_participant("owner")
        cls.other, cls.other_login = cls._portal_participant("other")
        cls.registration = cls.env["event.registration"].create(
            {"event_id": cls.event.id, "partner_id": cls.owner.id}
        )
        cls.registration.action_confirm()
        # The stage that asks for the passport
        cls.registration.stage_id = cls.env.ref(
            "website_switzerland.task_passport"
        ).stage_id
        cls.staff_login = f"t3572-staff-{cls.token}"
        cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": f"T3572 staff {cls.token}",
                "login": cls.staff_login,
                "password": cls.staff_login,
                "groups_id": [
                    (
                        6,
                        0,
                        (
                            cls.env.ref("base.group_user")
                            + cls.env.ref("event.group_event_user")
                            + cls.env.ref("child_protection.group_criminal_record")
                        ).ids,
                    )
                ],
            }
        )

    @classmethod
    def _portal_participant(cls, name):
        partner = cls.env["res.partner"].create(
            {
                "name": f"T3572 {name} {cls.token}",
                "email": f"t3572-{name}-{cls.token}@example.com",
                "lang": "en_US",
            }
        )
        login = f"t3572-{name}-{cls.token}"
        cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "login": login,
                "password": login,
                "partner_id": partner.id,
                "groups_id": [(6, 0, cls.env.ref("base.group_portal").ids)],
            }
        )
        return partner, login

    def _post(self, url, data, files=None):
        return self.url_open(
            url,
            data={"csrf_token": http.Request.csrf_token(self), **data},
            files=files,
        )

    def _edit(self, registration, document=FORGED, comment="Not my comment"):
        return self._post(
            "/my/events/form/registration_edit",
            {"registration_id": registration.id, "comments": comment},
            files={"passport": ("passport.pdf", document, "application/pdf")},
        )

    def _flight(self, registration, number):
        return self._post(
            "/my/events/form/flight",
            {
                "registration_id": registration.id,
                "flight_type": "outbound",
                "flying_company": "Swiss",
                "flight_number": number,
                "departure": "2027-03-01 08:00:00",
                "arrival": "2027-03-01 18:00:00",
            },
        )

    def _passport(self):
        return self.registration.partner_id.sudo().passport

    def _comments(self):
        return self.registration.message_ids.filtered(
            lambda m: m.author_id == self.owner and "comment" in (m.body or "")
        )

    # === Writes ===

    def test_the_generic_forms_are_closed(self):
        """Anyone used to reach these models through /website/form with any
        registration_id."""
        self.authenticate(None, None)
        for model in ("event.registration.form", "event.flight"):
            with self.subTest(model):
                response = self._post(
                    f"/website/form/{model}",
                    {
                        "registration_id": self.registration.id,
                        "comments": "Not my comment",
                        "flight_number": "XX666",
                        "flight_type": "outbound",
                        "departure": "2027-03-01 08:00:00",
                        "arrival": "2027-03-01 18:00:00",
                    },
                    files={"passport": ("passport.pdf", FORGED, "application/pdf")},
                )
                self.assertIn("error", json.loads(response.text))
        self.assertFalse(self._passport())
        self.assertFalse(self.registration.flight_ids)
        self.assertFalse(self._comments())

    def test_the_passport_task_is_asked(self):
        self.assertTrue(self.task(self.registration, "task_passport"))

    def test_another_participant_changes_nothing(self):
        self.authenticate(self.other_login, self.other_login)
        # 404, or 418 when the local 404 page fails to render
        self.assertNotEqual(self._edit(self.registration).status_code, 200)
        self.assertNotEqual(self._flight(self.registration, "XX666").status_code, 200)
        self.assertFalse(self._passport())
        self.assertFalse(self.task(self.registration, "task_passport").done)
        self.assertFalse(self.registration.flight_ids)
        self.assertFalse(self._comments())

    def test_a_visitor_changes_nothing(self):
        self.authenticate(None, None)
        self._edit(self.registration)
        self._flight(self.registration, "XX666")
        self.assertFalse(self._passport())
        self.assertFalse(self.registration.flight_ids)

    def test_the_participant_sends_their_documents_and_flight(self):
        self.authenticate(self.owner_login, self.owner_login)
        response = self._edit(self.registration, PASSPORT, "My own comment")
        self.assertEqual(response.status_code, 200)
        self.assertIn("id", json.loads(response.text))
        self.assertEqual(base64.b64decode(self._passport()), PASSPORT)
        self.assertTrue(self.task(self.registration, "task_passport").done)
        self.assertTrue(self._comments())
        # Entering the flight again corrects it, it never makes a second one
        self.assertEqual(self._flight(self.registration, "LX100").status_code, 200)
        self.assertEqual(self._flight(self.registration, "LX200").status_code, 200)
        self.assertEqual(
            self.registration.flight_ids.mapped("flight_number"), ["LX200"]
        )

    def test_portal_users_cannot_write_through_the_orm(self):
        """The forms are not the only way in: a portal user may call the
        models directly."""
        user = self.env["res.users"].search([("login", "=", self.other_login)])
        flight = self.env["event.flight"].create(
            {
                "registration_id": self.registration.id,
                "flight_type": "return",
                "flight_number": "LX300",
                "departure": "2027-03-10 08:00:00",
                "arrival": "2027-03-10 18:00:00",
            }
        )
        as_other = self.env(user=user)
        self.assertFalse(as_other["event.flight"].search([("id", "=", flight.id)]))
        with self.assertRaises(AccessError):
            as_other["event.flight"].browse(flight.id).write({"flight_number": "XX"})
        with self.assertRaises(AccessError):
            as_other["event.registration.form"].create(
                {"registration_id": self.registration.id, "comments": "forged"}
            )
        task = self.task(self.registration, "task_passport")
        with self.assertRaises(AccessError):
            as_other["event.registration.task.rel"].browse(task.id).write(
                {"done": True}
            )
        self.assertFalse(task.done)

    def test_a_task_of_someone_else_cannot_be_clicked(self):
        task = self.task(self.registration, "task_passport")
        self.authenticate(self.other_login, self.other_login)
        response = self.url_open(f"/my/events/tasks/{task.id}")
        self.assertNotEqual(response.status_code, 200)
        self.assertFalse(task.done)

    def test_the_registration_form_registers_the_logged_in_user(self):
        """partner_id and match_update came from the browser: a participant
        could register someone else and overwrite their data."""
        user = self.env["res.users"].search([("login", "=", self.other_login)])
        request = SimpleNamespace(env=self.env(user=user))
        values = self.env["event.registration"].website_form_input_filter(
            request, {"partner_id": self.owner.id, "match_update": True}
        )
        self.assertEqual(values, {"partner_id": self.other.id})
        public = SimpleNamespace(env=self.env(user=self.env.ref("base.public_user")))
        values = self.env["event.registration"].website_form_input_filter(
            public, {"partner_id": self.owner.id, "match_update": True}
        )
        self.assertEqual(values, {})

    # === Reads ===

    def _set_documents(self):
        self.owner.sudo().write(
            {"passport": base64.b64encode(PASSPORT), "criminal_record": PASSPORT_B64}
        )

    def test_documents_are_for_the_participant_and_the_staff(self):
        self._set_documents()
        self.registration.website_published = True
        urls = {
            "document route": f"/my/events/{self.registration.id}/document/passport",
            "registration": f"/web/content/event.registration/{self.registration.id}"
            "/passport",
            "partner": f"/web/content/res.partner/{self.owner.id}/passport",
            "criminal record": f"/web/content/event.registration/"
            f"{self.registration.id}/criminal_record",
        }
        for who, login in (("visitor", None), ("other", self.other_login)):
            self.authenticate(login, login)
            for name, url in urls.items():
                with self.subTest(who=who, url=name):
                    response = self.url_open(url, allow_redirects=False)
                    self.assertNotIn(PASSPORT, response.content)
        self.authenticate(self.owner_login, self.owner_login)
        for document in ("passport", "criminal_record"):
            response = self.url_open(
                f"/my/events/{self.registration.id}/document/{document}"
            )
            self.assertEqual(response.content, PASSPORT, document)
        # the staff of both groups
        self.authenticate(self.staff_login, self.staff_login)
        for url in urls.values():
            self.assertEqual(self.url_open(url).content, PASSPORT, url)

    def test_the_public_page_still_shows_the_participant(self):
        self._set_documents()
        self.registration.write(
            {
                "website_published": True,
                "profile_picture": self._picture(1200, 800),
                "profile_name": "Owner on the web",
            }
        )
        self.authenticate(None, None)
        page = self.url_open(self.registration.website_url)
        self.assertEqual(page.status_code, 200)
        self.assertIn("Owner on the web", page.text)
        photo = self.url_open(f"/event/registration/{self.registration.id}/photo")
        self.assertEqual(photo.status_code, 200)


PASSPORT_B64 = base64.b64encode(PASSPORT)
