##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import (
    ALLERGY_ANSWER,
    BIRTHDATE,
    CITY,
    EMERGENCY_NAME,
    FEEDBACK_ANSWER,
    FEEDBACK_RATING,
    FIRSTNAME,
    MEDICAL_ANSWER,
    MOTTO,
    PASSPORT_NUMBER,
    PORTAL_PAGE_LINK,
    REGISTRATION_FEE,
    SINGLE_ROOM_PRICE,
    STREET,
    TRIP_PRICE,
    ZIP,
    GroupVisitJourneyCase,
)


@tagged("post_install", "-at_install")
class TestGroupVisitJourney(GroupVisitJourneyCase):
    def test_group_visit_journey(self):
        registration = self._register_on_the_website()
        self._confirm_the_registration(registration)
        self._pay_the_registration_fee(registration)
        self._fill_the_documents(registration)
        self._fill_the_medical_survey(registration)
        self._invoice_and_pay_the_trip(registration)
        self._come_back_from_the_trip(registration)

    def _register_on_the_website(self):
        self.run_tour(self.compassion_event.website_url, "group_visit_registration")

        registration = self.get_registration()
        self.assertEqual(
            len(registration), 1, "The tour should have registered one participant"
        )

        partner = registration.partner_id
        self.assertEqual(partner.lastname, self.participant_lastname)
        self.assertEqual(partner.firstname, FIRSTNAME)
        self.assertEqual(partner.email, self.participant_email)
        self.assertEqual(partner.street, STREET)
        self.assertEqual(partner.zip, ZIP)
        self.assertEqual(partner.city, CITY)
        self.assertEqual(
            str(partner.birthdate_date),
            BIRTHDATE,
            "The birthdate of the form did not reach the contact",
        )
        self.assertEqual(registration.passport_number, PASSPORT_NUMBER)
        self.assertEqual(registration.emergency_name, EMERGENCY_NAME)
        self.assertTrue(registration.single_room)
        self.assertTrue(registration.profile_picture)
        self.assertEqual(registration.ambassador_quote.strip(), MOTTO)

        self.assertSentOnce(
            self.step1,
            "Registering should have sent the step1 registration confirmation",
        )

        invoice = registration.down_payment_id
        self.assertTrue(invoice, "Registering did not create the fee invoice")
        self.assertEqual(invoice.partner_id, partner)
        self.assertEqual(invoice.amount_total, REGISTRATION_FEE)
        self.assertEqual(invoice.state, "posted")
        self.assertEqual(invoice.payment_state, "not_paid")

        self.assertEqual(registration.stage_id, self.stage_down_payment)
        return registration

    def _confirm_the_registration(self, registration):
        self.run_tour("/odoo", "group_visit_confirmation", login="admin")
        registration.invalidate_recordset()
        self.assertEqual(registration.state, "open")
        self.assertEqual(registration.stage_id, self.stage_down_payment)

    def _pay_the_registration_fee(self, registration):
        self.pay(registration.down_payment_id)
        self.assertEqual(registration.down_payment_id.payment_state, "paid")

        self.assertTrue(
            self.task(registration, "task_down_payment").done,
            "Paying the fee should have completed the down payment task",
        )
        self.assertEqual(
            registration.stage_id,
            self.stage_agreements,
            "Paying the fee should have moved the participant to the agreements",
        )
        self.assertSentOnce(
            self.step2, "Paying the fee should have sent the documents to fill"
        )
        self.assertIn(
            PORTAL_PAGE_LINK,
            self.step2.email_template_id.with_context(
                lang=registration.partner_id.lang
            ).body_html,
            "The mail asking for the documents should link to the trip on the portal",
        )

    def _fill_the_documents(self, registration):
        self.run_tour(self.signup_url(registration.partner_id), "group_visit_documents")

        partner = registration.partner_id
        self.assertTrue(
            partner.user_ids, "Activating the account did not create a portal user"
        )
        self.assertTrue(partner.date_agreed_child_protection_charter)
        self.assertTrue(registration.passport, "The passport is missing from Odoo")
        self.assertTrue(
            registration.criminal_record, "The criminal record is missing from Odoo"
        )
        self.assertTrue(partner.passport)
        self.assertTrue(partner.criminal_record)

        for xmlid in (
            "task_activate_account",
            "task_sign_travel",
            "task_sign_child_protection",
            "task_passport",
            "task_criminal",
        ):
            self.assertTrue(
                self.task(registration, xmlid).done, f"{xmlid} was not ticked off"
            )

        self.assertEqual(registration.stage_id, self.stage_medical)
        self.assertSentOnce(
            self.step3, "Completing the documents should have sent the step3 mail"
        )

    def _fill_the_medical_survey(self, registration):
        registration.stage_date = fields.Date.today() - timedelta(days=10)
        self.run_event_schedulers()
        self.assertSentOnce(
            self.medical_invitation,
            "Ten days in the medical stage should have invited the participant"
            " to fill the medical survey",
        )

        self.run_tour(
            f"/my/events/{registration.id}",
            "group_visit_medical_survey",
            login=self.participant_login(registration),
        )

        answer = registration.medical_survey_id
        self.assertSurveyDone(
            answer,
            self.medical_survey,
            registration.partner_id,
            "The medical survey of the participant is missing",
        )
        self.assertEqual(
            answer.user_input_line_ids.suggested_answer_id.mapped("value"),
            [MEDICAL_ANSWER],
        )
        self.assertIn(
            ALLERGY_ANSWER,
            answer.user_input_line_ids.mapped("value_text_box"),
        )
        self.assertEqual(registration.survey_count, 1)
        self.assertTrue(
            self.task(registration, "task_medical_survey").done,
            "Filling the medical survey should have ticked its task off",
        )

    def _invoice_and_pay_the_trip(self, registration):
        self.run_tour("/odoo", "group_visit_trip_invoice", login="admin")
        registration.invalidate_recordset()

        self.assertTrue(
            self.task(registration, "task_medical_discharge").done,
            "The tour should have ticked the medical discharge off",
        )
        self.assertEqual(registration.stage_id, self.stage_payment)

        invoice = registration.trip_invoice_id
        self.assertTrue(invoice, "The tour should have invoiced the trip")
        self.assertEqual(invoice.partner_id, registration.partner_id)
        self.assertEqual(
            invoice.amount_total,
            TRIP_PRICE + SINGLE_ROOM_PRICE,
            "The participant asked for a single room, which is an extra fee",
        )
        self.assertEqual(invoice.state, "posted")

        self.assertSentOnce(
            self.travel_documents,
            "The tour should have sent the travel documents request",
        )

        # Paying the trip is the last task of the participant.
        self.pay(invoice)
        self.assertTrue(
            self.task(registration, "task_full_payment").done,
            "Paying the trip should have completed its task",
        )

    def _come_back_from_the_trip(self, registration):
        ended = fields.Datetime.now() - timedelta(days=15)
        started = ended - timedelta(days=10)
        self.compassion_event.write(
            {
                "start_date": started,
                "end_date": ended,
                # The children of the trip are held from before it starts.
                "hold_start_date": started.date() - timedelta(days=1),
            }
        )
        self.event.write({"date_begin": started, "date_end": ended})
        self.compassion_event.past_event_action()
        registration.invalidate_recordset()
        self.assertEqual(registration.stage_id, self.stage_attended)
        self.assertEqual(registration.state, "done")

        self.run_event_schedulers()
        self.assertSentOnce(
            self.feedback_request,
            "Two weeks after the trip the participant should be asked for feedback",
        )

        survey = self.event.feedback_survey_id
        self.run_tour(
            survey.get_start_url(),
            "group_visit_feedback_survey",
            login=self.participant_login(registration),
        )

        answer = registration.feedback_survey_id
        self.assertSurveyDone(
            answer,
            survey,
            registration.partner_id,
            "The feedback of the participant is missing",
        )
        self.assertEqual(
            set(answer.user_input_line_ids.suggested_answer_id.mapped("value")),
            {FEEDBACK_RATING},
            "Every part of the trip should have been rated",
        )
        self.assertIn(
            FEEDBACK_ANSWER, answer.user_input_line_ids.mapped("value_text_box")
        )
