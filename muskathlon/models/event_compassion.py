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
import re


class EventCompassion(models.Model):
    _inherit = 'crm.event.compassion'

    thank_you_text = fields.Html(translate=True)
    muskathlon_event_id = fields.Char(
        string="Muskathlon event ID", size=128)
    muskathlon_registration_ids = fields.One2many(
        'muskathlon.registration', 'event_id', 'Muskathlon registrations')

    public_description = fields.Text('Description publique')
    picture_1 = fields.Binary('Picture 1')
    picture_2 = fields.Binary('Picture 2')
    video_url = fields.Char("Video URL")
    participants_amount_objective = fields.Integer(
        'Default raise objective by participant', default=10000, require=True)
    amount_objective = fields.Integer(readonly=True,
                                      compute='_compute_amount_raised')
    amount_raised = fields.Integer(readonly=True,
                                   compute='_compute_amount_raised')
    amount_raised_percents = fields.Integer(readonly=True,
                                            compute='_compute_amount_raised')

    def _compute_amount_raised(self):
        for event in self:
            amount_raised = 0
            amount_objective = 0

            for registration in event.muskathlon_registration_ids:
                amount_raised += registration.amount_raised
                amount_objective += registration.amount_objective

            event.amount_raised = amount_raised
            event.amount_objective = amount_objective
            event.amount_raised_percents = int(
                amount_raised * 100 / amount_objective)

    @api.model
    def getEventParticipants(self, event_id):
        participants = self.env['muskathlon.registration'].search(
            [('event_id', '=', event_id)]
        )

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

    public_description = fields.Text('Public description')
    ambassador_quote_public = fields.Text("Ambassador public quote")
    picture_1 = fields.Binary('Picture 1')
    picture_2 = fields.Binary('Picture 2')
    sport_type = fields.Selection([
        ('run_21', 'Run 21 Km'),
        ('run_42', 'Run 42 Km'),
        ('run_60', 'Run 60 Km'),
        ('walk_60', 'Walk 60 Km'),
        ('climb', 'Climb'),
        ('bike_120', 'Bike 120 Km'),
        ('bike_400', 'Bike 400 Km')
    ], string='Sport', require=True)
    amount_objective = fields.Integer('Raise objective', default=10000,
                                      require=True)
    amount_raised = fields.Integer(readonly=True,
                                   compute='_compute_amount_raised')
    amount_raised_percents = fields.Integer(readonly=True,
                                            compute='_compute_amount_raised')

    muskathlon_participant_id = fields.Char(
        related='partner_id.muskathlon_participant_id')

    muskathlon_event_id = fields.Char(
        related='event_id.muskathlon_event_id')

    reg_id = fields.Char(string='Muskathlon registration ID', size=128)

    _sql_constraints = [
        ('reg_unique', 'unique(event_id,partner_id)',
         'Only one registration per participant/event is allowed!')
    ]

    def _compute_amount_raised(self):
        muskathlon_report = self.env['muskathlon.report']

        for registration in self:
            amount_raised = int(sum(
                item.amount for item in muskathlon_report.search([]) if
                item.user_id.id == registration.partner_id.id))

            registration.amount_raised = amount_raised
            registration.amount_raised_percents = int(
                amount_raised * 100 / registration.amount_objective)

    def get_sport_type_name(self):
        match = re.match(r'([a-z]{1,})(_([0-9]{1,}))?', self.sport_type)
        label = match.group(1).capitalize()

        if (match.group(2)):
            label += ' for ' + match.group(3) + ' Km'

        return label
