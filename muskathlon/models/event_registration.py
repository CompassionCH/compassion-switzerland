##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api, _
import datetime

from odoo.exceptions import UserError


class MuskathlonRegistration(models.Model):
    _name = "event.registration"
    _inherit = "event.registration"

    lead_id = fields.Many2one("crm.lead", "Lead", readonly=False)
    backup_id = fields.Integer(help="Old muskathlon registration id")
    is_muskathlon = fields.Boolean(related="compassion_event_id.website_muskathlon")
    sport_discipline_id = fields.Many2one(
        "sport.discipline", "Sport discipline", readonly=False
    )
    sport_level = fields.Selection(
        [("beginner", "Beginner"), ("average", "Average"), ("advanced", "Advanced")]
    )
    sport_level_description = fields.Text("Describe your sport experience")
    t_shirt_size = fields.Selection(
        related="partner_id.advocate_details_id.t_shirt_size", store=True
    )
    t_shirt_type = fields.Selection(
        related="partner_id.advocate_details_id.t_shirt_type", store=True
    )

    is_in_two_months = fields.Boolean(compute="_compute_is_in_two_months")

    _sql_constraints = [
        (
            "reg_unique",
            "unique(event_id,partner_id)",
            "Only one registration per participant/event is allowed!",
        )
    ]

    @api.model
    def create(self, values):
        # Automatically complete the task sign_child_protection if the charter
        # has already been signed.
        partner = self.env["res.partner"].browse(values.get("partner_id"))
        completed_tasks = values.setdefault("completed_task_ids", [])
        if partner and partner.has_agreed_child_protection_charter:
            task = self.env.ref("muskathlon.task_sign_child_protection")
            completed_tasks.append((4, task.id))
        if partner and partner.user_ids and any(partner.mapped("user_ids.login_date")):
            task = self.env.ref("muskathlon.task_activate_account")
            completed_tasks.append((4, task.id))
        return super(MuskathlonRegistration, self).create(values)

    @api.multi
    def _compute_step2_tasks(self):
        # Consider Muskathlon task for scan passport
        super(MuskathlonRegistration, self)._compute_step2_tasks()
        muskathlon_passport = self.env.ref("muskathlon.task_scan_passport")
        for reg in self:
            reg.passport_uploaded = muskathlon_passport in reg.completed_task_ids

    def _compute_amount_raised(self):
        # Use Muskathlon report to compute Muskathlon event donation
        m_reg = self.filtered("compassion_event_id.website_muskathlon")

        pids = m_reg.mapped("partner_id").ids
        origins = m_reg.mapped("compassion_event_id.origin_id")
        self.env.cr.execute("""
            SELECT sum(il.price_subtotal_signed) AS amount, il.user_id, il.event_id
            FROM account_invoice_line il
            left join product_product pp on pp.id=il.product_id 
            WHERE il.state = 'paid'
            and pp.default_code  = 'muskathlon'
            AND il.user_id = ANY(%s)
            AND il.event_id = ANY(%s)
            GROUP BY il.user_id, il.event_id
            UNION ALL
            SELECT sum(1000) AS amount, r.user_id, o.event_id
            FROM recurring_contract r
            JOIN recurring_contract_origin o ON r.origin_id = o.id
            WHERE r.user_id = ANY(%s)
            AND r.origin_id = ANY(%s)
            GROUP BY r.user_id, o.event_id
        """, [pids, origins.mapped("event_id").ids, pids, origins.ids])
        results = self.env.cr.dictfetchall()
        for registration in m_reg:
            registration.amount_raised = int(sum(
                r["amount"] for r in results
                if r["user_id"] == registration.partner_id_id
                and r["event_id"] == registration.compassion_event_id.id))

        super(MuskathlonRegistration, (self - m_reg))._compute_amount_raised()

    def _compute_is_in_two_months(self):
        """this function define is the bollean hide or not the survey"""
        for registration in self:
            today = datetime.datetime.today()
            start_day = registration.event_begin_date
            delta = start_day - today
            registration.is_in_two_months = delta.days < 60

    @api.onchange("event_id")
    def onchange_event_id(self):
        return {
            "domain": {
                "sport_discipline_id": [
                    ("id", "in", self.compassion_event_id.sport_discipline_ids.ids)
                ]
            }
        }

    @api.onchange("sport_discipline_id")
    def onchange_sport_discipline(self):
        if (
                self.sport_discipline_id
                and self.sport_discipline_id
                not in self.compassion_event_id.sport_discipline_ids
        ):
            self.sport_discipline_id = False
            return {
                "warning": {
                    "title": _("Invalid sport"),
                    "message": _("This sport is not in muskathlon"),
                }
            }

    def notify_new_registration(self):
        """Notify user for registration"""
        partners = self.mapped("user_id.partner_id") | self.event_id.mapped(
            "message_partner_ids"
        )
        self.message_subscribe(partners.ids)

        body = _("The participant registered through the Muskathlon website.")

        self.message_post(
            body=body,
            subject=_("%s - New Muskathlon registration") % self.name,
            message_type="email",
            subtype="website_event_compassion.mt_registration_create",
        )
        return True

    def muskathlon_medical_survey_done(self):
        for registration in self:
            user_input = self.env["survey.user_input"].search(
                [
                    ("partner_id", "=", registration.partner_id_id),
                    ("survey_id", "=", registration.event_id.medical_survey_id.id),
                ],
                limit=1,
            )

            registration.write(
                {
                    "completed_task_ids": [
                        (4, self.env.ref("muskathlon.task_medical").id)
                    ],
                    "medical_survey_id": user_input.id,
                }
            )

            # here we need to send a mail to the muskathlon doctor
            muskathlon_doctor_email = (
                self.env["ir.config_parameter"]
                    .sudo()
                    .get_param("muskathlon.doctor.email")
            )
            if muskathlon_doctor_email:
                template = (
                    self.env.ref("muskathlon.medical_survey_to_doctor_template")
                        .with_context(email_to=muskathlon_doctor_email)
                        .sudo()
                )
                try:
                    template.send_mail(
                        user_input.id,
                        force_send=True,
                        email_values={"email_to": muskathlon_doctor_email},
                    )
                except UserError:
                    continue
        return True
