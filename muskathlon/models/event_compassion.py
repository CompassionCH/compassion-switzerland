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
from odoo import models, fields


class EventCompassion(models.Model):
    _inherit = 'crm.event.compassion'

    thank_you_text = fields.Html(translate=True)

    muskathlon_event_id = fields.Char(
        string="Muskathlon event ID", size=128)
    muskathlon_registration_ids = fields.One2many(
        'muskathlon.registration', 'event_id', 'Muskathlon registrations')


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
