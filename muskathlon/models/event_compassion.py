# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class EventCompassion(models.Model):
    _inherit = 'crm.event.compassion'

    thank_you_text = fields.Html(translate=True)

    # public_description = fields.Char()

    muskathlon_event_id = fields.Char(
        string="Muskathlon event ID", size=128)
    muskathlon_registration_ids = fields.One2many(
        'muskathlon.registration', 'event_id', 'Muskathlon registrations')

    @api.model
    def getEventParticipants(self, event_id):
        participants = self.env['muskathlon.registration'].search([('event_id', '=', event_id)])

        # Convert to json compatible
        ret = []
        for participant in participants:
            ret.append({
                'id': participant.partner_id.id,
                'name': participant.partner_id.name,
                'gender': participant.partner_id.gender,
                'country': participant.partner_id.country_id.name
            })
        return ret


class MuskathlonRegistration(models.Model):
    _name = 'muskathlon.registration'
    _description = 'Muskathlon registration'
    _order = 'id desc'

    event_id = fields.Many2one(
        'crm.event.compassion', 'Muskathlon event',
    )
    partner_id = fields.Many2one(
        'res.partner', 'Muskathlon participant',
    )

    muskathlon_participant_id = fields.Char(
        related='partner_id.muskathlon_participant_id')

    muskathlon_event_id = fields.Char(
        related='event_id.muskathlon_event_id')

    reg_id = fields.Char(string='Muskathlon registration ID', size=128)

    _sql_constraints = [
        ('reg_unique', 'unique(event_id,partner_id)',
         'Only one registration per participant/event is allowed!')
    ]
