from odoo import models


class EventRegistration(models.Model):
    _inherit = "event.registration"

    def create(self, vals_list):
        registrations = super().create(vals_list)
        activate_task = self.env.ref("website_switzerland.task_activate_account")
        child_protection_task = self.env.ref(
            "website_switzerland.task_sign_child_protection"
        )
        for registration in registrations:
            partner = registration.partner_id
            if partner.user_ids and any(partner.mapped("user_ids.login_date")):
                registration.task_ids.filtered(
                    lambda t, m_task=activate_task: t.task_id == m_task
                ).write({"done": True})
            if partner.date_agreed_child_protection_charter:
                registration.task_ids.filtered(
                    lambda t, m_task=child_protection_task: t.task_id == m_task
                ).write({"done": True})
        return registrations

    def _inverse_passport(self):
        super()._inverse_passport()
        task_passport = self.env.ref("website_switzerland.task_passport")
        for registration in self.filtered("passport"):
            registration.task_ids.filtered(lambda t: t.task_id == task_passport).write(
                {"done": True}
            )
