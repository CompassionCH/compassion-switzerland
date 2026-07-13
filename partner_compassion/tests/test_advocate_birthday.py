from datetime import date, datetime
from unittest.mock import patch

from odoo.tests.common import TransactionCase


class TestAdvocateBirthday(TransactionCase):
    def setUp(self):
        super().setUp()
        self.Details = self.env["advocate.details"]
        self.translation_engagement = self.env.ref(
            "partner_compassion.engagement_translation"
        )
        self.event_engagement = self.env.ref("partner_compassion.engagement_event")
        self.sport_engagement = self.env.ref("partner_compassion.engagement_sport")

        self.icp = self.env["ir.config_parameter"].sudo()
        self.noemi = self.env["res.partner"].create({"name": "Noemi Test"})
        self.colin = self.env["res.partner"].create({"name": "Colin Test"})
        self.joelle = self.env["res.partner"].create({"name": "Joelle Test"})
        self.icp.set_param(
            "partner_compassion.advocate_birthday_translation_id", self.noemi.id
        )
        self.icp.set_param("partner_compassion.advocate_birthday_fr_id", self.joelle.id)
        self.icp.set_param("partner_compassion.advocate_birthday_de_id", self.colin.id)
        self.icp.set_param("partner_compassion.advocate_birthday_it_id", self.colin.id)
        self.icp.set_param("partner_compassion.advocate_birthday_en_id", self.joelle.id)

    def _create_advocate(self, lang, engagement, birthdate):
        partner = self.env["res.partner"].create(
            {"name": "Volunteer Test", "lang": lang, "birthdate_date": birthdate}
        )
        return self.Details.create(
            {
                "partner_id": partner.id,
                "state": "active",
                "engagement_ids": [(6, 0, engagement.ids)],
            }
        )

    def test_translation_volunteer_routed_to_translation_recipient(self):
        advocate = self._create_advocate(
            "fr_CH", self.translation_engagement, date(1990, 1, 1)
        )
        self.assertEqual(
            advocate._advocate_birthday_recipient_id(advocate), self.noemi.id
        )

    def test_event_volunteer_routed_by_language(self):
        advocate = self._create_advocate(
            "de_DE", self.event_engagement, date(1990, 1, 1)
        )
        self.assertEqual(
            advocate._advocate_birthday_recipient_id(advocate), self.colin.id
        )

    def test_sport_volunteer_no_longer_dropped(self):
        # Sport used to be unconditionally excluded from all reminders.
        advocate = self._create_advocate(
            "fr_CH", self.sport_engagement, date(1990, 1, 1)
        )
        self.assertEqual(
            advocate._advocate_birthday_recipient_id(advocate), self.joelle.id
        )

    def test_unconfigured_language_falls_back_to_general_recipients(self):
        self.icp.set_param("partner_compassion.advocate_birthday_it_id", "")
        advocate = self._create_advocate(
            "it_IT", self.event_engagement, date(1990, 1, 1)
        )
        recipient = advocate._advocate_birthday_recipient_id(advocate)
        self.assertIn(recipient, {self.colin.id, self.joelle.id})

    @patch("odoo.addons.partner_compassion.models.advocate_details.datetime")
    def test_weekend_birthdays_bundled_into_tuesdays_run(self, mock_datetime):
        # Tuesday 2026-07-14 + 3 business days = Friday 2026-07-17.
        mock_datetime.today.return_value = datetime(2026, 7, 14)
        friday = self._create_advocate(
            "fr_CH", self.event_engagement, date(1990, 7, 17)
        )
        saturday = self._create_advocate(
            "fr_CH", self.event_engagement, date(1990, 7, 18)
        )
        sunday = self._create_advocate(
            "fr_CH", self.event_engagement, date(1990, 7, 19)
        )
        monday = self._create_advocate(
            "fr_CH", self.event_engagement, date(1990, 7, 20)
        )

        self.Details.advocate_cron()

        for advocate in (friday, saturday, sunday):
            self.assertTrue(
                advocate.message_ids.filtered("subject"),
                f"expected a birthday reminder for advocate {advocate.id}",
            )
        self.assertFalse(monday.message_ids.filtered("subject"))

    @patch("odoo.addons.partner_compassion.models.advocate_details.datetime")
    def test_non_friday_run_does_not_bundle_weekend(self, mock_datetime):
        # Monday 2026-07-13 + 3 business days = Thursday 2026-07-16.
        mock_datetime.today.return_value = datetime(2026, 7, 13)
        saturday = self._create_advocate(
            "fr_CH", self.event_engagement, date(1990, 7, 18)
        )

        self.Details.advocate_cron()

        self.assertFalse(saturday.message_ids.filtered("subject"))
