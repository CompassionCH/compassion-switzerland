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
    flight_price = fields.Float(compute='_compute_total_price')
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
    # Don't configure any e-mail by default
    event_mail_ids = fields.One2many('event.mail', default=False)
    faq_category_ids = fields.Many2many(
        'event.faq.category', compute='_compute_faq_category_ids')

    visa_needed = fields.Boolean()
    months_needed_for_a_visa = fields.Integer()
    medical_survey_id = fields.Many2one('survey.survey', 'Medical Survey')
    feedback_survey_id = fields.Many2one('survey.survey', 'Feedback Survey')

    def _compute_total_price(self):
        flight = self.env.ref(
            'website_event_compassion.product_template_flight')
        flight_product = self.env['product.product'].search([
            ('product_tmpl_id', '=', flight.id)
        ])
        for event in self:
            tickets = event.mapped('event_ticket_ids')
            event.total_price = sum(tickets.mapped('price') or [0])
            event.flight_price = sum(
                tickets.filtered(
                    lambda t: t.product_id == flight_product)
                .mapped('price') or [0]
            )

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

    def _compute_faq_category_ids(self):
        for event in self:
            event.faq_category_ids = self.env['event.faq.category'].search([
                '|', ('event_type_ids', '=', event.event_type_id.id),
                ('event_type_ids', '=', False)
            ])

    def _default_tickets(self):
        """ Add flight and single room supplement by default. """
        res = super(Event, self)._default_tickets()
        room = self.env.ref(
            'website_event_compassion.product_template_single_room')
        flight = self.env.ref(
            'website_event_compassion.product_template_flight')
        trip = self.env.ref(
            'website_event_compassion.product_template_trip_price')
        products = self.env['product.product'].search([
            ('product_tmpl_id', 'in', (room + flight + trip).ids)])
        res.extend([{
            'name': product.name,
            'product_id': product.id,
            'price': 0,
        } for product in products])
        return res

    def mail_attendees(self, template_id, force_send=False, filter_func=None):
        """
        Never use this function (replaced by execute method in event_email.py
        :return: True
        """
        return True
