##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Sebastien Toth <popod@me.com>
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime, timedelta
from odoo import models, fields, api


class EventCompassion(models.Model):
    _name = 'crm.event.compassion'
    _inherit = ['crm.event.compassion', 'website.published.mixin',
                'translatable.model', 'website.seo.metadata']

    muskathlon_event_id = fields.Char(
        string="Muskathlon event ID", size=128)
    registration_ids = fields.One2many(
        'event.registration', 'compassion_event_id', 'Event registrations')

    amount_objective = fields.Integer(compute='_compute_amount_raised')
    amount_raised = fields.Integer(compute='_compute_amount_raised')
    amount_raised_percents = fields.Integer(compute='_compute_amount_raised')
    sport_discipline_ids = fields.Many2many(
        'sport.discipline', string='Sport disciplines')

    website_muskathlon = fields.Boolean(
        'Activate Muskathlon template',
        help='This will activate the 4M red template for the event on the'
             'website and will also use the Muskathlon processes for the'
             'registrations.')
    # HTML fields for material order page
    website_my_introduction = fields.Html(
        string='Video introduction', translate=True, sanitize=False)
    website_my_fundraising = fields.Html(
        string='Fundraising', translate=True, sanitize=False)
    website_my_information = fields.Html(
        string='Event information', translate=True, sanitize=False)
    website_my_press_material = fields.Html(
        string='Press material', translate=True, sanitize=False)
    website_my_sport_material = fields.Html(
        string='Sport material', translate=True, sanitize=False)

    @api.multi
    def _compute_amount_raised(self):
        for event in self:
            amount_raised = 0
            amount_objective = 0

            for registration in event.registration_ids:
                amount_raised += registration.amount_raised
                amount_objective += registration.amount_objective

            event.amount_raised = amount_raised
            event.amount_objective = amount_objective
            event.amount_raised_percents = int(
                amount_raised * 100 / (amount_objective or 1))

    @api.multi
    @api.depends('event_type_id')
    def _compute_event_type(self):
        # Map Muskathlon event type
        super(EventCompassion, self)._compute_event_type()
        muskathlon = self.env.ref('muskathlon.event_type_muskathlon')
        for event in self.filtered(lambda e: e.event_type_id == muskathlon):
            event.type = 'sport'

    @api.model
    def get_muskathlon_participants(self, event_id):
        participants = self.env['event.registration'].search(
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

    @api.model
    def _cron_delete_medical_surveys(self):
        for event in self.search(
                [('end_date', '<', fields.Datetime.to_string(
                    datetime.now() - timedelta(days=31)))]):
            for registration in event.registration_ids:
                # the deletion will cascade to the different
                # user_input_line automatically (see postgres)
                registration.medical_survey_id.unlink()
