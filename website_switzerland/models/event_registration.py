from odoo import api, models


class EventRegistration(models.Model):
    _inherit = "event.registration"

    @api.model_create_multi
    def create(self, vals_list):
        registrations = super().create(vals_list)
        for registration in registrations:
            partner = registration.partner_id
            if not partner.country_id:
                partner.country_id = self.env.ref("base.ch")
        registrations.create_down_payment()
        return registrations

    def write(self, vals):
        super().write(vals)
        if vals.get("passport"):
            task_passport = self.env.ref("website_switzerland.task_passport")
            self.mapped("task_ids").filtered(
                lambda t: t.task_id == task_passport
            ).write({"done": True})
        medical_stage = self.env.ref("website_switzerland.stage_group_medical")
        if vals.get("stage_id") == medical_stage.id:
            for registration in self.filtered(lambda r: not r.medical_survey_id):
                registration.create_medical_survey()
        ready_stage = self.env.ref("website_switzerland.stage_group_ready")
        if vals.get("stage_id") == ready_stage.id:
            for registration in self.filtered(lambda r: not r.feedback_survey_id):
                registration.create_feedback_survey()
        return True

    def create_medical_survey(self):
        self.ensure_one()
        survey = self.event_id.medical_survey_id
        if survey and not self.medical_survey_id:
            survey_input = (
                self.env["survey.user_input"]
                .sudo()
                .create(
                    {
                        "survey_id": survey.id,
                        "partner_id": self.partner_id.id,
                        "state": "new",
                    }
                )
            )
            self.medical_survey_id = survey_input.id

    def create_feedback_survey(self):
        self.ensure_one()
        survey = self.event_id.feedback_survey_id
        if survey and not self.feedback_survey_id:
            survey_input = (
                self.env["survey.user_input"]
                .sudo()
                .create(
                    {
                        "survey_id": survey.id,
                        "partner_id": self.partner_id.id,
                        "state": "new",
                    }
                )
            )
            self.feedback_survey_id = survey_input.id
