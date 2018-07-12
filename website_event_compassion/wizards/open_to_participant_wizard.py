# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class OpenEventToParticipant(models.TransientModel):
    """ This wizard generates a Gift Invoice for a given contract. """
    _name = 'crm.event.compassion.open.wizard'
    _description = 'Open event to participants wizard'

    registration_fee = fields.Float()
    seats_min = fields.Integer('Minimum participants required')
    seats_max = fields.Integer('Maximum participants allowed')
    reply_to = fields.Char('E-mail replies to',
                           default=lambda s: s._default_reply())

    def _default_reply(self):
        event = self.env['crm.event.compassion'].browse(
            self.env.context.get('active_id'))
        return event.user_id.email or self.env.user.email

    @api.multi
    def open_event(self):
        event = self.env['crm.event.compassion'].browse(
            self.env.context.get('active_id'))
        event_type_id = False
        if event.type == 'sport':
            event_type_id = self.env.ref(
                'website_event_compassion.event_type_sport').id
        elif event.type == 'tour':
            event_type_id = self.env.ref(
                'website_event_compassion.event_type_tour').id
        elif event.type == 'meeting':
            event_type_id = self.env.ref(
                'website_event_compassion.event_type_meeting').id
        odoo_event = self.env['event.event'].create({
            'name': event.name,
            'event_type_id': event_type_id,
            'user_id': event.user_id.id,
            'date_begin': event.start_date,
            'date_end': event.end_date,
            'seats_min': self.seats_min,
            'seats_max': self.seats_max,
            'seats_availability': self.seats_max and 'limited' or 'unlimited',
            'reply_to': self.reply_to
        })
        event.write({
            'registration_fee': self.registration_fee,
            'odoo_event_id': odoo_event.id
        })
        return {
            'name': 'Event',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'event.event',
            'res_id': odoo_event.id,
            'context': self.env.context,
            'target': 'current',
        }
