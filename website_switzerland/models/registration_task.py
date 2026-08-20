from odoo import models


class RegistrationTaskRel(models.Model):
    _inherit = "event.registration.task.rel"

    def _compute_task_url(self):  # pylint: disable=missing-return
        super()._compute_task_url()
        travel_contract = self.env.ref("website_switzerland.task_sign_travel")
        task_charter = self.env.ref("website_switzerland.task_sign_child_protection")
        task_criminal = self.env.ref("website_switzerland.task_criminal")
        task_passport = self.env.ref("website_switzerland.task_passport")
        task_medic = self.env.ref("website_switzerland.task_medical_survey")
        slug = self.env["ir.http"]._slug
        for task in self:
            if task.task_id == travel_contract:
                task.task_url = (
                    f"/my/events/{slug(task.registration_id)}/travel_agreement"
                )
            elif task.task_id == task_charter:
                task.task_url = (
                    f"/partner/child-protection-charter?redirect="
                    f"/my/events/{slug(task.registration_id)}"
                )
            elif task.task_id == task_criminal:
                task.task_url = f"/my/events/{slug(task.registration_id)}/criminal"
            elif task.task_id == task_passport:
                task.task_url = f"/my/events/{slug(task.registration_id)}/passport"
            elif task.task_id == task_medic:
                survey = (
                    task.registration_id.medical_survey_id
                    or task.registration_id.event_id.medical_survey_id
                )
                task.task_url = (
                    survey.get_print_url() if task.done else survey.get_start_url()
                )
