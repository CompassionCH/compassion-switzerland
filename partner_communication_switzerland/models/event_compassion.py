# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
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
        'muskathlon.registration', 'event_id')


class MuskathlonRegistration(models.Model):
    _name = 'muskathlon.registration'

    event_id = fields.Many2one(comodel_name='crm.event.compassion',
                               string='Muskathlon event')
    partner_id = fields.Many2one(
        comodel_name='res.partner', string='Muskathlon participant')

    muskathlon_participant_id = fields.Char(
        related='partner_id.muskathlon_participant_id')

    muskathlon_event_id = fields.Char(
        related='event_id.muskathlon_event_id')

    reg_id = fields.Char(string='Muskathlon registration ID', size=128)
