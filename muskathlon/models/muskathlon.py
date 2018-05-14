# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api
from odoo.tools import config
from odoo.exceptions import MissingError


class MuskathlonDetails(models.Model):
    _inherit = "ambassador.details"

    # emergency relation type selection
    ERT_SELECTION = [('husband', 'Husband'),
                     ('wife', 'Wife'),
                     ('father', 'Father'),
                     ('mother', 'Mother'),
                     ('brother', 'Brother'),
                     ('sister', 'Sister'),
                     ('son', 'Son'),
                     ('daughter', 'Daughter'),
                     ('friend', 'Friend'),
                     ('other', 'Other')]

    TSHIRT_SELECTION = [
        ('S', 'S'), ('M', 'M'), ('L', 'L'), ('XL', 'XL'), ('XXL', 'XXL')
    ]

    emergency_name = fields.Char('Emergency contact name')
    emergency_phone = fields.Char('Emergency contact phone number')
    emergency_relation_type = fields.Selection(ERT_SELECTION,
                                               string='Emergency contact '
                                                      'relation type')
    birth_name = fields.Char()
    passport_number = fields.Char()
    passport_expiration_date = fields.Date()
    message_when_donation = fields.Boolean()
    tshirt_size = fields.Selection(TSHIRT_SELECTION)

    sql_constraints = [
        ('partner_unique', 'UNIQUE (partner_id)', 'Partner must be unique.')
    ]


class MuskathlonRegistration(models.Model):
    _name = 'muskathlon.registration'
    _description = 'Muskathlon registration'
    _order = 'id desc'

    event_id = fields.Many2one(
        'crm.event.compassion', 'Muskathlon event', required=True,
        domain="[('type', '=', 'sport')]"
    )
    partner_id = fields.Many2one(
        'res.partner', 'Muskathlon participant', required=True
    )
    ambassador_details_id = fields.Many2one(
        'ambassador.details', related='partner_id.ambassador_details_id')

    # The 4 following fields avoid giving read access to the public on the
    # res.partner participating in the muskathlon.
    partner_id_id = fields.Integer(related="partner_id.id", readonly=True)
    partner_display_name = fields.Char(related="partner_id.display_name",
                                       readonly=True)
    partner_preferred_name = fields.Char(related="partner_id.preferred_name",
                                         readonly=True)
    partner_name = fields.Char(related="partner_id.name", readonly=True)
    ambassador_picture_1 = fields.Binary(
        related='ambassador_details_id.picture_1', readonly=True)
    ambassador_picture_2 = fields.Binary(
        related='ambassador_details_id.picture_2', readonly=True)
    ambassador_description = fields.Text(
        related='ambassador_details_id.description', readonly=True)
    ambassador_quote = fields.Text(
        related='ambassador_details_id.quote', readonly=True)
    ambassador_thank_you_quote = fields.Html(
        related='ambassador_details_id.thank_you_quote', readonly=True)
    partner_gender = fields.Selection(related='partner_id.title.gender',
                                      readonly=True)

    sport_discipline_id = fields.Many2one('sport.discipline', required=True)
    amount_objective = fields.Integer('Raise objective', default=10000,
                                      required=True)
    amount_raised = fields.Integer(readonly=True,
                                   compute='_compute_amount_raised')
    amount_raised_percents = fields.Integer(readonly=True,
                                            compute='_compute_amount_raised')

    muskathlon_participant_id = fields.Char(
        related='partner_id.muskathlon_participant_id')

    muskathlon_event_id = fields.Char(
        related='event_id.muskathlon_event_id')

    reg_id = fields.Char(string='Muskathlon registration ID', size=128)
    host = fields.Char(compute='_compute_host', readonly=True)

    _sql_constraints = [
        ('reg_unique', 'unique(event_id,partner_id)',
         'Only one registration per participant/event is allowed!')
    ]

    def _compute_amount_raised(self):
        muskathlon_report = self.env['muskathlon.report']

        for registration in self:
            amount_raised = int(sum(
                item.amount for item in muskathlon_report.search([
                    ('user_id', '=', registration.partner_id.id)
                ])
            ))

            registration.amount_raised = amount_raised
            registration.amount_raised_percents = int(
                amount_raised * 100 / registration.amount_objective)

    def _compute_host(self):
        host = config.get('wordpress_host')
        if not host:
            raise MissingError(_('Missing wordpress_host in odoo config file'))
        for registration in self:
            registration.host = host

    def get_sport_discipline_name(self):
        return self.sport_discipline_id.get_label()

    @api.onchange('event_id')
    def onchange_event_id(self):
        return {
            'domain': {'sport_discipline': [('id', 'in', self.event_id.sport_discipline_ids.ids)]}
        }

    @api.onchange('sport_discipline')
    def onchange_sport_discipline(self):
        if self.sport_discipline and self.sport_discipline not in self.event_id.sport_discipline_ids:
            self.sport_discipline = False
            return {
                'warning': {
                    'title': _('Invalid sport'),
                    'message': _('This sport is not in muskathlon')
                }
            }
