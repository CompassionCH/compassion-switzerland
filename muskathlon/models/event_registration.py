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
    t_shirt_size = fields.Selection(
        related='partner_id.advocate_details_id.t_shirt_size', store=True)
    t_shirt_type = fields.Selection(
        related='partner_id.advocate_details_id.t_shirt_type', store=True)
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
    def notify_new_registration(self):
        """Notify user for registration"""
        self._message_auto_subscribe_notify(
            self.mapped('user_id.partner_id').ids)
        return True
