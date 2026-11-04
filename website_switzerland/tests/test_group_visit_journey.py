##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import timedelta

from odoo import Command, fields, http
from odoo.tests import tagged

from odoo.addons.base.models.ir_actions_report import IrActionsReport

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
    def setUp(self):
        super().setUp()
        if self._testMethodName != "test_group_visit_journey":
            # The stages don't need the payment slips, which take minutes to
            # print.
            self.patch(
                IrActionsReport,
                "_render_qweb_pdf",
                lambda report, report_ref, res_ids=None, data=None: (
                    b"%PDF-1.4",
                    "pdf",
                ),
            )

    def test_group_visit_journey(self):
        registration = self._register_on_the_website()
        self._check_the_registration_in_the_backend()
        self._pay_the_registration_fee(registration)
        self._check_the_public_profile()
        self._activate_the_account(registration)
        self._book_the_flights(registration)
        self._fill_the_documents(registration)
        self._fill_the_medical_survey(registration)
        self._invoice_and_pay_the_trip(registration)
        self._send_the_criminal_record(registration)
        self._come_back_from_the_trip(registration)

    def test_sent_confirmation_registers(self):
        registration = self._new_registration("Registered")
        job = self._communications(self.step1, registration.partner_id)
        self.assertEqual(job.state, "done")
        self.assertEqual(registration.stage_id, self.stage_registered)
        self.assertEqual(registration.state, "draft")
        self.assertTrue(
            self.task(registration, "task_down_payment"),
            "Registered should ask for the fee",
        )

    def test_paid_fee_confirms_and_opens_the_account(self):
        registration = self._new_registration("Paying")
        partner = registration.partner_id
        self.pay(registration.down_payment_id)

        self.assertEqual(registration.stage_id, self.stage_confirmed)
        self.assertEqual(registration.state, "open")
        user = partner.user_ids
        self.assertEqual(len(user), 1, "Paying the fee should open the account")
        self.assertTrue(user._is_portal())
        self.assertTrue(self._communications(self.step3, partner))
        self.assertFalse(
            self.task(registration, "task_activate_account").done,
            "The participant still has to activate the account",
        )
        self.assertEqual(
            registration.stage_id,
            self.stage_confirmed,
            "Confirmed waits for the flights to be set by hand",
        )

    def test_fee_paid_online_confirms(self):
        registration = self._new_registration("Paying online")
        self.assertTrue(self.task(registration, "task_down_payment"))
        self.pay_online(registration.down_payment_id)
        self.assertEqual(registration.down_payment_id.payment_state, "paid")
        self.assertTrue(
            self.task(registration, "task_down_payment").done,
            "Paying the fee on the portal should tick the fee off",
        )
        self.assertEqual(registration.stage_id, self.stage_confirmed)

    def test_paid_fee_without_email(self):
        registration = self._new_registration("No email", email=False)
        self.assertEqual(
            registration.stage_id,
            self.stage_unconfirmed,
            "The registration confirmation cannot be sent without an e-mail",
        )
        self.pay(registration.down_payment_id)
        self.assertEqual(registration.stage_id, self.stage_unconfirmed)

        # Staff sees it in Unconfirmed and sends the confirmation by post.
        registration.stage_id = self.stage_registered
        self.assertEqual(
            registration.stage_id,
            self.stage_confirmed,
            "The fee paid before is not asked again",
        )
        self.assertFalse(registration.partner_id.user_ids)
        self.assertTrue(
            any(
                "no e-mail address" in (message.body or "")
                for message in registration.message_ids
            ),
            "Staff should be told the account could not be opened",
        )

    def test_paid_fee_reactivates_the_account(self):
        registration = self._new_registration("Came back")
        partner = registration.partner_id
        user = (
            self.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "login": f"came-back-{self.token}",
                    "partner_id": partner.id,
                    "groups_id": [Command.set(self.env.ref("base.group_portal").ids)],
                }
            )
        )
        user.active = False
        self.pay(registration.down_payment_id)
        self.assertTrue(user.active, "The archived account should be opened again")
        self.assertEqual(partner.with_context(active_test=False).user_ids, user)

    def test_flights_then_documents(self):
        registration = self._confirmed_registration("Flying")
        partner = registration.partner_id
        registration.stage_id = self.stage_flights
        self.assertTrue(self._communications(self.flights_request, partner))
        self.assertTrue(self.task(registration, "task_flight_details").task_url)
        self.assertTrue(self.task(registration, "task_return_flight").task_url)

        self._enter_the_flights(registration, "outbound")
        self.assertTrue(self.task(registration, "task_flight_details").done)
        self.assertFalse(self.task(registration, "task_return_flight").done)
        self.assertEqual(
            registration.stage_id,
            self.stage_flights,
            "Flights should wait for the return flight",
        )
        self._enter_the_flights(registration, "return")
        self.assertTrue(self.task(registration, "task_return_flight").done)
        self.assertEqual(registration.stage_id, self.stage_documents)
        self.assertTrue(self._communications(self.step2, partner))
        self.assertTrue(registration.medical_survey_id)
        self.assertFalse(
            self.task(registration, "task_criminal"),
            "The criminal record is asked once the trip is paid",
        )

    def test_trip_invoice_then_criminal_record(self):
        registration = self._confirmed_registration("Paying the trip")
        partner = registration.partner_id
        registration.stage_id = self.stage_documents
        registration.task_ids.filtered(
            lambda rel: rel.stage_id == self.stage_documents
        ).done = True
        self.assertEqual(
            registration.stage_id,
            self.stage_documents,
            "Payment waits for the trip to be invoiced",
        )

        registration.create_trip_invoice()
        self.assertEqual(registration.stage_id, self.stage_payment)
        self.assertTrue(self._communications(self.travel_documents, partner))

        self.pay(registration.trip_invoice_id)
        self.assertEqual(
            registration.stage_id,
            self.stage_criminal_record,
            "Trip paid is passed through once the trip is paid",
        )
        self.assertTrue(self._communications(self.criminal_record_request, partner))

        partner.write({"criminal_record": self._picture(10, 10)})
        self.assertEqual(registration.stage_id, self.stage_ready)
        self.assertFalse(
            self._communications(self.feedback_request, partner),
            "Nothing is sent before Attended",
        )

    def test_payment_set_by_hand_invoices_the_trip(self):
        registration = self._confirmed_registration("Dragged to payment")
        registration.stage_id = self.stage_payment
        invoice = registration.trip_invoice_id
        self.assertTrue(invoice, "Setting Payment by hand should invoice the trip")
        self.assertTrue(
            self._communications(self.travel_documents, registration.partner_id)
        )

        registration.stage_id = self.stage_documents
        registration.stage_id = self.stage_payment
        self.assertEqual(
            registration.trip_invoice_id, invoice, "The trip is invoiced only once"
        )

    def test_attended_set_by_hand(self):
        registration = self._confirmed_registration("Back home")
        registration.stage_id = self.stage_documents
        self.assertTrue(registration.medical_survey_id)
        survey_answer = registration.medical_survey_id

        registration.stage_id = self.stage_attended
        self.assertEqual(registration.state, "done")
        self.assertTrue(
            self._communications(self.feedback_request, registration.partner_id)
        )
        self.assertTrue(registration.feedback_survey_id)
        self.assertFalse(
            survey_answer.exists(), "The medical answers are not kept after the trip"
        )

    def test_reminder_to_participants_with_something_to_do(self):
        late = self._confirmed_registration("Late")
        late.stage_id = self.stage_documents
        done = self._confirmed_registration("Done")
        done.stage_id = self.stage_documents
        done.task_ids.filtered(lambda rel: rel.task_id.website_published).done = True

        self.event.action_send_reminder()
        self.assertTrue(self._communications(self.reminder, late.partner_id))
        self.assertFalse(self._communications(self.reminder, done.partner_id))

    def test_two_trips_get_their_own_confirmation(self):
        self.step1.send_mode = "digital"
        partner = self._new_partner("Two trips")
        other_trip = self.event.copy({"name": f"Other trip {self.token}"})
        first, second = self.env["event.registration"].create(
            [
                {"event_id": self.event.id, "partner_id": partner.id},
                {"event_id": other_trip.id, "partner_id": partner.id},
            ]
        )
        jobs = self._communications(self.step1, partner)
        self.assertEqual(
            sorted(jobs.mapped("object_ids")), sorted([str(first.id), str(second.id)])
        )

    def test_stage_set_by_hand_sends_its_mail(self):
        registration = self._confirmed_registration("Moved by hand")
        registration.stage_id = self.stage_flights
        self.assertTrue(
            self._communications(self.flights_request, registration.partner_id),
            "Setting the flights stage by hand should ask for the flights",
        )

    def test_travel_contract_signs_only_its_trip(self):
        partner = self._new_partner("Two trips")
        login = f"two-trips-{self.token}"
        self.env["res.users"].with_context(no_reset_password=True).create(
            {
                "login": login,
                "password": login,
                "partner_id": partner.id,
                "groups_id": [(6, 0, self.env.ref("base.group_portal").ids)],
            }
        )
        other_trip = self.event.copy({"name": f"Other trip {self.token}"})
        signed, other = self.env["event.registration"].create(
            [
                {"event_id": self.event.id, "partner_id": partner.id},
                {"event_id": other_trip.id, "partner_id": partner.id},
            ]
        )
        (signed + other).action_confirm()
        (signed + other).write({"stage_id": self.stage_documents.id})

        self.authenticate(login, login)
        self.url_open(
            "/my/events/travel_contract",
            data={
                "csrf_token": http.Request.csrf_token(self),
                "registration_id": signed.id,
                "accept": "on",
            },
        )
        self.assertTrue(self.task(signed, "task_sign_travel").done)
        self.assertFalse(
            self.task(other, "task_sign_travel").done,
            "Accepting the contract of one trip should not sign the other one",
        )

    def _new_partner(self, name, email=True):
        slug = name.lower().replace(" ", "-")
        return self.env["res.partner"].create(
            {
                "name": f"{name} {self.token}",
                "email": email and f"{slug}-{self.token}@example.com",
                "lang": "en_US",
                # The payment slips need an address.
                "street": STREET,
                "zip": ZIP,
                "city": CITY,
            }
        )

    def _new_registration(self, name, email=True):
        return self.env["event.registration"].create(
            {
                "event_id": self.event.id,
                "partner_id": self._new_partner(name, email).id,
            }
        )

    def _confirmed_registration(self, name):
        registration = self._new_registration(name)
        self.pay(registration.down_payment_id)
        self.assertEqual(registration.stage_id, self.stage_confirmed)
        return registration

    def _enter_the_flights(self, registration, *flight_types):
        flight_types = flight_types or ("outbound", "return")
        departure = fields.Datetime.now() + timedelta(days=120)
        self.env["event.flight"].create(
            [
                {
                    "registration_id": registration.id,
                    "flight_type": flight_type,
                    "flying_company": "Swiss",
                    "flight_number": number,
                    "departure": departure + timedelta(days=days),
                    "arrival": departure + timedelta(days=days, hours=9),
                }
                for flight_type, number, days in (
                    ("outbound", "LX 1", 0),
                    ("return", "LX 2", 10),
                )
                if flight_type in flight_types
            ]
        )

    def _communications(self, config, partner):
        return self.env["partner.communication.job"].search(
            [("config_id", "=", config.id), ("partner_id", "=", partner.id)]
        )

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

        self.assertEqual(
            registration.stage_id,
            self.stage_registered,
            "Sending the registration confirmation should register the participant",
        )
        self.assertEqual(registration.state, "draft")
        return registration

    def _check_the_registration_in_the_backend(self):
        self.run_tour("/odoo", "group_visit_registration_check", login="admin")

    def _check_the_public_profile(self):
        self.run_tour("/odoo", "group_visit_public_profile", login="admin")

    def _pay_the_registration_fee(self, registration):
        self.pay(registration.down_payment_id)
        self.assertEqual(registration.down_payment_id.payment_state, "paid")

        self.assertTrue(
            self.task(registration, "task_down_payment").done,
            "Paying the fee should have completed the down payment task",
        )
        self.assertEqual(
            registration.stage_id,
            self.stage_confirmed,
            "Paying the fee should have confirmed the registration",
        )
        self.assertEqual(registration.state, "open")
        self.assertTrue(
            registration.partner_id.user_ids,
            "Paying the fee should have opened the MyCompassion account",
        )
        self.assertSentOnce(self.step3, "Paying the fee should have sent step3")

    def _activate_the_account(self, registration):
        self.run_tour(
            self.signup_url(registration.partner_id), "group_visit_account_activation"
        )
        self.assertTrue(self.task(registration, "task_activate_account").done)
        self.assertEqual(
            registration.stage_id,
            self.stage_confirmed,
            "The participant waits for the flights to be set by hand",
        )

    def _book_the_flights(self, registration):
        registration.stage_id = self.stage_flights
        self.assertSentOnce(
            self.flights_request, "Reaching Flights should have asked for the flights"
        )
        self._enter_the_flights(registration)
        self.assertEqual(registration.stage_id, self.stage_documents)
        self.assertSentOnce(
            self.step2, "Reaching Fill documents should have sent the step2 mail"
        )
        self.assertIn(
            PORTAL_PAGE_LINK,
            self.step2.email_template_id.with_context(
                lang=registration.partner_id.lang
            ).body_html,
            "The mail asking for the documents should link to the trip on the portal",
        )

    def _fill_the_medical_survey(self, registration):
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
            "Invoicing the trip should have sent the travel documents request",
        )

        # Paying the trip is the last task of the participant.
        self.pay(invoice)
        self.assertTrue(
            self.task(registration, "task_full_payment").done,
            "Paying the trip should have completed its task",
        )
        self.assertEqual(
            registration.stage_id,
            self.stage_criminal_record,
            "Paying the trip should have asked for the criminal record",
        )
        self.assertSentOnce(
            self.criminal_record_request,
            "Reaching Criminal record should have asked for it",
        )

    def _fill_the_documents(self, registration):
        self.run_tour(
            f"/my/events/{registration.id}",
            "group_visit_documents",
            login=self.participant_login(registration),
        )

        partner = registration.partner_id
        self.assertTrue(partner.date_agreed_child_protection_charter)
        self.assertTrue(registration.passport, "The passport is missing from Odoo")
        self.assertTrue(partner.passport)
        for xmlid in (
            "task_sign_travel",
            "task_sign_child_protection",
            "task_passport",
        ):
            self.assertTrue(
                self.task(registration, xmlid).done, f"{xmlid} was not ticked off"
            )
        self.assertEqual(registration.stage_id, self.stage_documents)

    def _send_the_criminal_record(self, registration):
        self.run_tour(
            f"/my/events/{registration.id}",
            "group_visit_criminal_record",
            login=self.participant_login(registration),
        )
        partner = registration.partner_id
        self.assertTrue(
            registration.criminal_record, "The criminal record is missing from Odoo"
        )
        self.assertTrue(partner.criminal_record)
        self.assertTrue(self.task(registration, "task_criminal").done)
        self.assertEqual(
            registration.stage_id,
            self.stage_ready,
            "The participant is ready to fly once the criminal record is sent",
        )

    def _come_back_from_the_trip(self, registration):
        medical_answer = registration.medical_survey_id
        # The coordinator sets the participants who came to Attended.
        registration.stage_id = self.stage_attended
        self.assertEqual(registration.state, "done")
        self.assertFalse(
            medical_answer.exists(), "The medical answers are not kept after the trip"
        )
        self.assertSentOnce(
            self.feedback_request,
            "Setting the participant to Attended should ask for feedback",
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
