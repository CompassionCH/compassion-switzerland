# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api, _
from odoo.addons.queue_job.job import job, related_action
import datetime


class MuskathlonRegistration(models.Model):
    _name = 'event.registration'
    _inherit = 'event.registration'

    lead_id = fields.Many2one('crm.lead', 'Lead')
    backup_id = fields.Integer(help='Old muskathlon registration id')
    is_muskathlon = fields.Boolean(
        related='compassion_event_id.website_muskathlon')
    sport_discipline_id = fields.Many2one(
        'sport.discipline', 'Sport discipline',
    )
    sport_level = fields.Selection([
        ('beginner', 'Beginner'),
        ('average', 'Average'),
        ('advanced', 'Advanced')
    ])
    sport_level_description = fields.Text('Describe your sport experience')
    t_shirt_size = fields.Selection(
        related='partner_id.advocate_details_id.t_shirt_size', store=True)
    t_shirt_type = fields.Selection(
        related='partner_id.advocate_details_id.t_shirt_type', store=True)
    muskathlon_participant_id = fields.Char(
        related='partner_id.muskathlon_participant_id')
    muskathlon_event_id = fields.Char(
        related='compassion_event_id.muskathlon_event_id')
    reg_id = fields.Char(string='Muskathlon registration ID', size=128)

    is_in_two_months = fields.Boolean(compute='_compute_is_in_two_months')

    _sql_constraints = [
        ('reg_unique', 'unique(event_id,partner_id)',
         'Only one registration per participant/event is allowed!')
    ]

    @api.model
    def create(self, values):
        # Automatically complete the task sign_child_protection if the charter
        # has already been signed.
        partner = self.env['res.partner'].browse(values.get('partner_id'))
        completed_tasks = values.setdefault('completed_task_ids', [])
        if partner and partner.has_agreed_child_protection_charter:
            task = self.env.ref('muskathlon.task_sign_child_protection')
            completed_tasks.append((4, task.id))
        if partner and partner.user_ids and any(
                partner.mapped('user_ids.login_date')):
            task = self.env.ref('muskathlon.task_activate_account')
            completed_tasks.append((4, task.id))
        return super(MuskathlonRegistration, self).create(values)

    def _compute_amount_raised(self):
        # Use Muskathlon report to compute Muskathlon event donation
        muskathlon_report = self.env['muskathlon.report']
        m_reg = self.filtered('compassion_event_id.website_muskathlon')
        for registration in m_reg:
            amount_raised = int(sum(
                item.amount for item in muskathlon_report.search([
                    ('user_id', '=', registration.partner_id.id),
                    ('event_id', '=', registration.compassion_event_id.id),
                ])
            ))
            registration.amount_raised = amount_raised
        super(MuskathlonRegistration, (self - m_reg))._compute_amount_raised()

    def _compute_is_in_two_months(self):
        """this function define is the bollean hide or not the survey"""
        for registration in self:
            today = datetime.date.today()
            start_day = fields.Date.from_string(registration.event_begin_date)
            delta = start_day - today
            registration.is_in_two_months = delta.days < 60

    @api.onchange('event_id')
    def onchange_event_id(self):
        return {
            'domain': {'sport_discipline_id': [
                ('id', 'in',
                 self.compassion_event_id.sport_discipline_ids.ids)]}
        }

    @api.onchange('sport_discipline_id')
    def onchange_sport_discipline(self):
        if self.sport_discipline_id and self.sport_discipline_id not in \
                self.compassion_event_id.sport_discipline_ids:
            self.sport_discipline_id = False
            return {
                'warning': {
                    'title': _('Invalid sport'),
                    'message': _('This sport is not in muskathlon')
                }
            }

    @job(default_channel='root.muskathlon')
    @related_action('related_action_registration')
    def notify_new_registration(self):
        """Notify user for registration"""
        partners = self.mapped('user_id.partner_id') | self.event_id.mapped(
            'message_partner_ids')
        self.message_subscribe(partners.ids)
        self.message_post(
            body=_(
                "The participant registered through the Muskathlon website."),
            subject=_("%s - New Muskathlon registration") % self.name,
            message_type='email',
            subtype="website_event_compassion.mt_registration_create"
        )
        return True

    @job(default_channel='root.muskathlon')
    @related_action('related_action_registration')
    def muskathlon_medical_survey_done(self):
        for registration in self:
            user_input = self.env['survey.user_input'].search([
                ('partner_id', '=', registration.partner_id_id),
                ('survey_id', '=',
                 registration.event_id.medical_survey_id.id)
            ], limit=1)

            registration.write({
                'completed_task_ids': [
                    (4, self.env.ref('muskathlon.task_medical').id)
                ],
                'medical_survey_id': user_input.id
            })

            # here we need to send a mail to the muskathlon doctor
            muskathlon_doctor_email = self.env[
                'ir.config_parameter'].get_param('muskathlon.doctor.email')
            if muskathlon_doctor_email:
                template = self.env \
                    .ref("muskathlon.medical_survey_to_doctor_template") \
                    .with_context(email_to=muskathlon_doctor_email).sudo()
                template.send_mail(
                    user_input.id, force_send=True, email_values={
                        'email_to': muskathlon_doctor_email
                    })
        return True
