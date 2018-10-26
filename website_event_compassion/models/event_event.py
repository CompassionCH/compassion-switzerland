# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

from odoo import models, fields


class Event(models.Model):
    _inherit = 'event.event'

    compassion_event_id = fields.Many2one(
        'crm.event.compassion', 'Event')
    total_price = fields.Float(compute='_compute_total_price')
    participants_amount_objective = fields.Integer(
        'Default raise objective by participant', default=10000)
    custom_amount_objective = fields.Boolean(
        'Participant can set his raising objective'
    )
    fundraising = fields.Boolean(
        'Activate fundraising for participants',
        help='If activated, the participants will have a user account where '
             'they can keep track of their donations. They will have a '
             'profile page on the website where people can donate.'
    )
    donation_product_id = fields.Many2one(
        'product.product', 'Donation product'
    )
    sponsorship_donation_value = fields.Float(
        'Sponsorship to CHF donation conversion',
        default=1000,
        help='This sets how much the barometer of the participant will be '
             'raised when a sponsorship is made for him.'
    )
    registration_open = fields.Boolean(
        compute='_compute_registration_open'
    )
    registration_closed = fields.Boolean(
        compute='_compute_registration_closed')
    registration_not_started = fields.Boolean(
        compute='_compute_registration_not_started'
    )
    registration_full = fields.Boolean(
        compute='_compute_registration_full'
    )
    valid_ticket_ids = fields.Many2many('event.event.ticket',
                                        compute='_compute_valid_tickets')

    def _compute_total_price(self):
        for event in self:
            event.total_price = sum(
                event.mapped('event_ticket_ids.price') or [0])

    def _compute_valid_tickets(self):
        for event in self:
            event.valid_ticket_ids = event.mapped('event_ticket_ids').filtered(
                lambda t: not t.is_expired and
                (t.seats_available or t.seats_availability == 'unlimited')
            )

    def _compute_registration_open(self):
        for event in self:
            start_date = fields.Datetime.from_string(event.date_begin)
            event.registration_open = event.state == 'confirm' and \
                event.valid_ticket_ids and datetime.now() < start_date

    def _compute_registration_closed(self):
        for event in self:
            start_date = fields.Datetime.from_string(event.date_begin)
            event.registration_closed = event.state == 'done' or \
                start_date < datetime.now() or not event.valid_ticket_ids

    def _compute_registration_not_started(self):
        for event in self:
            event.registration_not_started = event.state == 'draft' or not \
                event.event_ticket_ids

    def _compute_registration_full(self):
        for event in self:
            start_date = fields.Datetime.from_string(event.date_begin)
            event.registration_full = event.state == 'confirm' and \
                datetime.now() < start_date and not event.valid_ticket_ids
