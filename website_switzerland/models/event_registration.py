from odoo import api, models


class EventRegistration(models.Model):
    _inherit = "event.registration"

    @api.model_create_multi
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
        return True
g