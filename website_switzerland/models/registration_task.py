from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class RegistrationTaskRel(models.Model):
    _inherit = "event.registration.task.rel"

    def _compute_task_url(self):  # pylint: disable=missing-return
        super()._compute_task_url()
        travel_contract = self.env.ref("website_switzerland.task_sign_travel")
        task_charter = self.env.ref("website_switzerland.task_sign_child_protection")
        task_criminal = self.env.ref("website_switzerland.task_criminal")
        task_passport = self.env.ref("website_switzerland.task_passport")
        task_medic = self.env.ref("website_switzerland.task_medical_survey")
        task_flight = self.env.ref(
            "website_switzerland.task_flight_details"
        ) + self.env.ref("website_switzerland.task_return_flight")
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
            elif task.task_id in task_flight:
                task.task_url = f"/my/events/{slug(task.registration_id)}/flight"
            elif task.task_id == task_medic:
                survey = (
                    task.registration_id.medical_survey_id
                    or task.registration_id.event_id.medical_survey_id
                )
                task.task_url = (
                    survey.get_print_url() if task.done else survey.get_start_url()
                )

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        create_account = self.env.ref("website_switzerland.task_activate_account")
        child_protection = self.env.ref(
            "website_switzerland.task_sign_child_protection"
        )
        passport = self.env.ref("website_switzerland.task_passport")
        criminal = self.env.ref("website_switzerland.task_criminal")
        flights = {
            self.env.ref("website_switzerland.task_flight_details"): "outbound",
            self.env.ref("website_switzerland.task_return_flight"): "return",
        }
        # An invoice paid before its stage was reached (e.g. the registration
        # confirmation could not be sent) must not be asked again.
        paid_invoices = {
            self.env.ref("website_switzerland.task_down_payment"): "down_payment_id",
            self.env.ref("website_switzerland.task_full_payment"): "trip_invoice_id",
        }
        for task in tasks:
            invoice_field = paid_invoices.get(task.task_id)
            if invoice_field and task.registration_id[invoice_field].payment_state in (
                "paid",
                "in_payment",
            ):
                task.write({"done": True})
            if (
                task.task_id == create_account
                and task.registration_id.partner_id.user_ids.filtered("login_date")
            ):
                task.write({"done": True})
            if (
                task.task_id == child_protection
                and task.registration_id.partner_id.date_agreed_child_protection_charter
            ):
                task.write({"done": True})
            # The passport is confidential (T3572): whoever creates the task
            # need not be allowed to read it.
            if task.task_id == passport and task.registration_id.sudo().passport:
                task.write({"done": True})
            flight_type = flights.get(task.task_id)
            if flight_type and flight_type in task.registration_id.flight_ids.mapped(
                "flight_type"
            ):
                task.write({"done": True})
            if task.task_id == criminal:
                criminal_record_date = (
                    task.registration_id.partner_id.criminal_record_date
                )
                # The criminal record should be recent
                today = fields.Date.today()
                if criminal_record_date and (
                    criminal_record_date >= today - relativedelta(months=12)
                ):
                    task.write({"done": True})
        return tasks
