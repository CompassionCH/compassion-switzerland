# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api
from odoo.addons.website.models.website import slug


class EventCompassion(models.Model):
    _name = 'crm.event.compassion'
    _inherit = ['crm.event.compassion', 'website.published.mixin',
                'translatable.model', 'website.seo.metadata']

    name = fields.Char(translate=True)
    website_description = fields.Html(translate=True, sanitize=False)
    thank_you_text = fields.Html(translate=True)
    picture_1 = fields.Binary('Banner image', attachment=True)
    filename_1 = fields.Char(compute='_compute_filenames')
    website_side_info = fields.Html(
        string='Side info', translate=True, sanitize=False
    )
    odoo_event_id = fields.Many2one('event.event')
    seats_expected = fields.Integer(related='odoo_event_id.seats_expected')

    @api.multi
    def _compute_website_url(self):
        for event in self:
            event.website_url = "/event/{}".format(slug(event))

    @api.multi
    def _compute_filenames(self):
        for event in self:
            event.filename_1 = event.name + '-1.jpg'

    def open_registrations(self):
        """
        This will create an event.event record and link it to the Compassion
        Event. It's useful for adding participants and managing e-mails
        and participant list.
        :return: action opening the wizard
        """
        return {
            'name': 'Open event registrations',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crm.event.compassion.open.wizard',
            'context': self.env.context,
            'target': 'new',
        }

    def open_participants(self):
        return {
            'name': 'Manage participants',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'event.registration',
            'domain': [('event_id', '=', self.odoo_event_id.id)],
            'context': self.with_context(
                default_compassion_event_id=self.id).env.context,
            'target': 'current',
        }
