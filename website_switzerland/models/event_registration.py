from odoo import Command, _, api, models


class EventRegistration(models.Model):
    _inherit = "event.registration"

    @api.model_create_multi
    def create(self, vals_list):
        registrations = super().create(vals_list)
        for registration in registrations:
            partner = registration.partner_id
            if not partner.country_id:
                partner.country_id = self.env.ref("base.ch")
        return registrations

    def write(self, vals):
        super().write(vals)
        if vals.get("passport"):
            task_passport = self.env.ref("website_switzerland.task_passport")
            self.mapped("task_ids").filtered(
                lambda t: t.task_id == task_passport
            ).write({"done": True})
        confirmed = self.env.ref("website_event_compassion.stage_all_confirmed")
        group_visit = self.env.ref("website_switzerland.event_type_group_visit")
        if vals.get("stage_id") == confirmed.id:
            # Paying the fee confirms the registration and opens the
            # MyCompassion account of the participant.
            for registration in self.filtered(
                lambda r: r.event_id.event_type_id == group_visit
                and not r.partner_id.user_ids
            ):
                registration.with_delay_sh(
                    "_create_portal_user",
                    identity_key=f"event.registration._create_portal_user."
                    f"{registration.partner_id.id}",
                )
        medical_stage = self.env.ref("website_switzerland.stage_group_medical")
        if vals.get("stage_id") == medical_stage.id:
            for registration in self.filtered(lambda r: not r.medical_survey_id):
                registration.create_medical_survey()
        attended = self.env.ref("website_event_compassion.stage_all_attended")
        if vals.get("stage_id") == attended.id:
            for registration in self.filtered(lambda r: not r.feedback_survey_id):
                registration.create_feedback_survey()
        return True

    def create_trip_invoice(self):
        """Creating the invoice of the trip moves the participants to the
        payment of the trip."""
        res = super().create_trip_invoice()
        payment = self.env.ref("website_switzerland.stage_group_documents")
        self.filtered(
            lambda r: r.trip_invoice_id
            and r.stage_id in r.event_id._registration_stages()
            and r.stage_id.sequence < payment.sequence
            and payment in r.event_id._registration_stages()
        ).write({"stage_id": payment.id})
        return res

    def _create_portal_user(self):
        """Open the MyCompassion account of the participant: my_compassion
        sends the activation link when the user is created."""
        self.ensure_one()
        partner = self.partner_id
        users = (
            self.env["res.users"]
            .sudo()
            .with_context(active_test=False)
            .search([("partner_id", "=", partner.id)])
        )
        if users.filtered("active"):
            return True
        if users:
            users[:1].active = True
            users[:1].action_reset_password()
            return True
        login = partner.email and partner.email.strip().lower()
        if not login:
            self.message_post(
                body=_(
                    "The MyCompassion account of the participant could not be "
                    "created: the partner has no e-mail address."
                )
            )
            return False
        if (
            self.env["res.users"]
            .sudo()
            .with_context(active_test=False)
            .search_count([("login", "=", login)])
        ):
            self.message_post(
                body=_(
                    "The MyCompassion account of the participant could not be "
                    "created: the login %s is already used by another account.",
                    login,
                )
            )
            return False
        self.env["res.users"].sudo().create(
            {
                "login": login,
                "partner_id": partner.id,
                "groups_id": [Command.set(self.env.ref("base.group_portal").ids)],
            }
        )
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
