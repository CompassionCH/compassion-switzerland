# -*- coding: utf-8 -*-
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
from odoo import models, fields, api
from odoo.addons.website.models.website import slug


class EventCompassion(models.Model):
    _name = 'crm.event.compassion'
    _inherit = ['crm.event.compassion', 'website.published.mixin']

    thank_you_text = fields.Html(translate=True)
    muskathlon_event_id = fields.Char(
        string="Muskathlon event ID", size=128)
    muskathlon_registration_ids = fields.One2many(
        'muskathlon.registration', 'event_id', 'Muskathlon registrations')

    website_description = fields.Html(translate=True,
                                      oldname='public_description')
    picture_1 = fields.Binary('Banner image', attachment=True)
    filename_1 = fields.Char(compute='_compute_filenames')
    participants_amount_objective = fields.Integer(
        'Default raise objective by participant', default=10000, required=True)
    amount_objective = fields.Integer(compute='_compute_amount_raised')
    amount_raised = fields.Integer(compute='_compute_amount_raised')
    amount_raised_percents = fields.Integer(compute='_compute_amount_raised')
    sport_discipline_ids = fields.Many2many('sport.discipline')

    @api.multi
    def _compute_website_url(self):
        for event in self:
            event.website_url = "/event/{}".format(slug(event))

    @api.multi
    def _compute_filenames(self):
        for event in self:
            event.filename_1 = event.name + '-1.jpg'

    @api.multi
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
    def get_event_participants(self, event_id):
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
