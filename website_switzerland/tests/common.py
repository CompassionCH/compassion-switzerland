##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import base64
import io
from datetime import timedelta
from uuid import uuid4

from PIL import Image

from odoo import Command, fields
from odoo.tests import HttpCase

from odoo.addons.base.models.ir_actions_report import IrActionsReport
from odoo.addons.partner_communication_switzerland.tests.common import (
    check_queue_runs,
    setup_tour_admin,
)

_pre_render_qweb_pdf = IrActionsReport._pre_render_qweb_pdf


def _force_pdf_rendering(self, report_ref, res_ids=None, data=None):
    return _pre_render_qweb_pdf(
        self.with_context(force_report_rendering=True), report_ref, res_ids, data
    )


REGISTRATION_FEE = 250
TRIP_PRICE = 3400
SINGLE_ROOM_PRICE = 600
RAISE_OBJECTIVE = 2000

FIRSTNAME = "Jane"
MOTTO = "I am going to meet my sponsored child!"
BIRTHDATE = "1985-04-23"
STREET = "Rue Galilee 3"
ZIP = "1400"
CITY = "Yverdon-les-Bains"
PASSPORT_NUMBER = "X1234567"
EMERGENCY_NAME = "Emergency Contact"

PORTAL_PAGE_LINK = "/my/events/{{registration.id}}"

MEDICAL_QUESTION = "Do you have a health issue we should know about"
MEDICAL_ANSWER = "I have back problems"
ALLERGY_QUESTION = "Tell us about your allergies"
ALLERGY_ANSWER = "pollen"

FEEDBACK_RATING = "Excellent"
FEEDBACK_ANSWER = "Nothing to improve, it was a life changing trip"

THEME_ASSETS = (
    "theme_compassion_2025/static/src/js/components/RangeInput.js",
    "theme_compassion_2025/static/src/js/components/ProgressBar.js",
    "theme_compassion_2025/static/src/xml/RangeInput.xml",
    "theme_compassion_2025/static/src/xml/ProgressBar.xml",
)


def setup_event_website(env):
    """Makes the event pages servable to the browser of a tour."""
    env["website"].search([]).domain = False
    env["ir.asset"].create(
        [
            {
                "name": f"Tour: {path.rsplit('/', 1)[-1]}",
                "bundle": "web.assets_frontend",
                "path": path,
            }
            for path in THEME_ASSETS
        ]
    )


class GroupVisitJourneyCase(HttpCase):
    """An announced group visit, ready to take registrations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        check_queue_runs(cls.env)

        cls.token = uuid4().hex[:8]

        cls.admin = setup_tour_admin(cls.env)
        cls.admin.groups_id |= cls.env.ref("child_protection.group_criminal_record")
        setup_event_website(cls.env)

        cls.bank_journal = cls.env["account.journal"].create(
            {
                "name": f"Group visit tour bank {cls.token}",
                "code": f"T{cls.token[:4]}",
                "type": "bank",
            }
        )

        cls.event_type = cls.env.ref("website_switzerland.event_type_group_visit")
        cls.stage_down_payment = cls.env.ref("website_switzerland.stage_group_pay")
        cls.stage_agreements = cls.env.ref(
            "website_switzerland.stage_group_unconfirmed"
        )
        cls.stage_medical = cls.env.ref("website_switzerland.stage_group_medical")
        cls.stage_payment = cls.env.ref("website_switzerland.stage_group_documents")
        cls.stage_attended = cls.env.ref("website_event_compassion.stage_all_attended")

        cls.step1 = cls.env.ref("website_switzerland.group_visit_step1_config")
        cls.step2 = cls.env.ref("website_switzerland.group_visit_step2_config")
        cls.step3 = cls.env.ref("website_switzerland.group_visit_step3_config")
        cls.medical_invitation = cls.env.ref(
            "website_switzerland.group_visit_medical_survey_config"
        )
        cls.travel_documents = cls.env.ref(
            "website_switzerland.group_visit_travel_documents_config"
        )
        cls.feedback_request = cls.env.ref(
            "website_switzerland.group_visit_after_trip_feedback_config"
        )

        cls.classPatch(IrActionsReport, "_pre_render_qweb_pdf", _force_pdf_rendering)

        cls._enable_portal_templates()
        cls._pin_registration_stages()
        cls._pin_communication_rules()
        cls._create_event()
        cls._create_medical_survey()
        cls._silence_other_events()

    @classmethod
    def _enable_portal_templates(cls):
        (
            cls.env.ref("website_switzerland.my_event_include_forms")
            + cls.env.ref("website_switzerland.travel_agreement")
        ).active = True

    @classmethod
    def _pin_registration_stages(cls):
        journey = (
            cls.stage_down_payment
            + cls.stage_agreements
            + cls.stage_medical
            + cls.stage_payment
        )
        for sequence, stage in enumerate(journey, start=1):
            stage.write(
                {
                    "sequence": sequence,
                    "event_type_ids": [Command.link(cls.event_type.id)],
                }
            )
        shared = {
            cls.env.ref("website_event_compassion.stage_all_confirmed"): 20,
            cls.stage_attended: 30,
            cls.env.ref("website_event_compassion.stage_all_cancelled"): 40,
        }
        for stage, sequence in shared.items():
            stage.write({"sequence": sequence, "event_type_ids": [Command.clear()]})

        strays = cls.env["event.registration.stage"].search(
            [
                ("event_type_ids", "=", False),
                ("id", "not in", [stage.id for stage in shared]),
            ]
        )
        if strays:
            other_type = cls.env["event.type"].create(
                {"name": "Stages of no group visit", "compassion_event_type": "meeting"}
            )
            strays.event_type_ids = [Command.link(other_type.id)]

    @classmethod
    def _pin_communication_rules(cls):
        expected = {
            cls.step1: (False, "after_sub", "now", 1),
            cls.step2: (cls.stage_agreements, "after_stage", "now", 1),
            cls.step3: (cls.stage_medical, "after_stage", "now", 1),
            cls.medical_invitation: (cls.stage_medical, "after_stage", "days", 10),
            cls.feedback_request: (False, "after_event", "days", 14),
        }
        for config, (stage, interval_type, unit, nbr) in expected.items():
            scheduler = cls.event_type.event_type_mail_ids.filtered(
                lambda m, c=config: m.communication_id == c
            )
            assert scheduler, (
                f"The {config.name} rule is missing from the "
                f"{cls.event_type.name} registration template"
            )
            scheduler.write(
                {
                    "stage_id": stage and stage.id,
                    "interval_type": interval_type,
                    "interval_unit": unit,
                    "interval_nbr": nbr,
                }
            )

    @classmethod
    def _create_event(cls):
        start = fields.Datetime.now() + timedelta(days=120)
        cls.compassion_event = cls.env["crm.event.compassion"].create(
            {
                "name": f"Group Visit Journey {cls.token} (tour)",
                "type": "tour",
                "event_type_id": cls.event_type.id,
                "start_date": start,
                "end_date": start + timedelta(days=10),
                "country_id": cls.env.ref("base.bo").id,
                "website_published": True,
                "picture_1": cls._picture(400, 300),
            }
        )
        wizard = (
            cls.env["crm.event.compassion.open.wizard"]
            .with_context(active_id=cls.compassion_event.id)
            .create(
                {
                    "registration_fee": REGISTRATION_FEE,
                    "product_id": cls.env.ref("event_product.product_product_event").id,
                    "fundraising": True,
                    "participants_amount_objective": RAISE_OBJECTIVE,
                }
            )
        )
        wizard.open_event()
        cls.event = cls.compassion_event.odoo_event_id
        cls.event.write(
            {
                "stage_id": cls.env.ref("event.event_stage_announced").id,
                "event_ticket_ids": [
                    Command.create(
                        {
                            "name": "Travel costs",
                            "price": TRIP_PRICE,
                            "product_id": cls.env.ref(
                                "website_event_compassion.product_template_trip_price"
                            ).product_variant_id.id,
                        }
                    ),
                    Command.create(
                        {
                            "name": "Single room",
                            "price": SINGLE_ROOM_PRICE,
                            "product_id": cls.env.ref(
                                "website_event_compassion.product_template_single_room"
                            ).product_variant_id.id,
                        }
                    ),
                ],
            }
        )

    @classmethod
    def _create_medical_survey(cls):
        cls.medical_survey = cls.env["survey.survey"].create(
            {
                "title": f"Medical survey {cls.token} (tour)",
                "questions_layout": "one_page",
                "access_mode": "public",
                "users_login_required": True,
                "question_and_page_ids": [
                    Command.create(
                        {
                            "title": MEDICAL_QUESTION,
                            "question_type": "simple_choice",
                            "constr_mandatory": True,
                            "suggested_answer_ids": [
                                Command.create({"value": "No health issue at all"}),
                                Command.create({"value": MEDICAL_ANSWER}),
                            ],
                        }
                    ),
                    Command.create(
                        {
                            "title": ALLERGY_QUESTION,
                            "question_type": "text_box",
                        }
                    ),
                ],
            }
        )
        cls.event.medical_survey_id = cls.medical_survey

    @classmethod
    def _silence_other_events(cls):
        cls.env["event.mail"].search(
            [("event_id", "!=", cls.event.id), ("mail_done", "=", False)]
        ).mail_done = True

    @staticmethod
    def _picture(width, height):
        """A plain PNG, as base64, of the given size."""
        picture = io.BytesIO()
        Image.new("RGB", (width, height), "#0054A6").save(picture, "PNG")
        return base64.b64encode(picture.getvalue())

    def run_tour(self, path, tour, login=None):
        """Starts a tour on a url that carries the token of the run."""
        separator = "&" if "?" in path else "?"
        self.start_tour(
            f"{path}{separator}tour_token={self.token}", tour, login=login, timeout=180
        )

    @property
    def participant_email(self):
        return f"group.visit.{self.token}@tour.example.org"

    @property
    def participant_lastname(self):
        return f"Doe{self.token}"

    def get_registration(self):
        return self.env["event.registration"].search([("event_id", "=", self.event.id)])

    def signup_url(self, partner):
        partner = partner.sudo()
        partner.signup_prepare()
        return partner.with_context(relative_url=True)._get_signup_url()

    def participant_login(self, registration):
        user = registration.partner_id.user_ids
        self.assertEqual(len(user), 1, "the participant should have one account")
        user.sudo().password = user.login
        return user.login

    def run_event_schedulers(self):
        self.env["event.mail"].sudo().schedule_communications()

    def task(self, registration, xmlid):
        task = self.env.ref(f"website_switzerland.{xmlid}")
        return registration.task_ids.filtered(lambda rel: rel.task_id == task)

    def pay(self, invoice):
        self.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=invoice.ids
        ).create({"journal_id": self.bank_journal.id})._create_payments()

    def assertSentOnce(self, config, msg):
        communication = self.env["partner.communication.job"].search(
            [
                ("config_id", "=", config.id),
                ("partner_id", "=", self.get_registration().partner_id.id),
            ]
        )
        self.assertEqual(len(communication), 1, msg)
        self.assertEqual(communication.state, "done", communication.body_html)
        return communication

    def assertSurveyDone(self, answer, survey, partner, msg):
        self.assertTrue(answer, msg)
        self.assertEqual(answer.survey_id, survey)
        self.assertEqual(answer.partner_id, partner)
        self.assertEqual(answer.state, "done")
