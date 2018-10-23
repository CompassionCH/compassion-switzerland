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
    muskathlon_participant_id = fields.Char(
        related='partner_id.muskathlon_participant_id')
    muskathlon_event_id = fields.Char(
        related='compassion_event_id.muskathlon_event_id')
    reg_id = fields.Char(string='Muskathlon registration ID', size=128)

    _sql_constraints = [
        ('reg_unique', 'unique(event_id,partner_id)',
         'Only one registration per participant/event is allowed!')
    ]

    def _compute_amount_raised(self):
        # Use Muskathlon report to compute Muskathlon event donation
        muskathlon_report = self.env['muskathlon.report']
        m_reg = self.filtered('compassion_event_id.website_muskathlon')
        for registration in m_reg:
            amount_raised = int(sum(
                item.amount for item in muskathlon_report.search([
                    ('user_id', '=', registration.partner_id.id),
                    ('event_id', '=', registration.compassion_event_id.id),
                    ('registration_id', '=', registration.reg_id),
                ])
            ))
            registration.amount_raised = amount_raised
        super(MuskathlonRegistration, (self - m_reg))._compute_amount_raised()

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
    def create_muskathlon_lead(self):
        """Create Muskathlon lead for registration"""
        self.ensure_one()
        partner = self.partner_id
        staff_id = self.env['staff.notification.settings'].get_param(
            'muskathlon_lead_notify_id')
        self.lead_id = self.env['crm.lead'].create({
            'name': u'Muskathlon Registration - ' + partner.name,
            'partner_id': partner.id,
            'email_from': partner.email,
            'phone': partner.phone,
            'partner_name': partner.name,
            'street': partner.street,
            'zip': partner.zip,
            'city': partner.city,
            'user_id': staff_id,
            'description': self.sport_level_description,
            'event_id': self.compassion_event_id.id,
            'sales_team_id': self.env.ref(
                'sales_team.salesteam_website_sales').id
        })
