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


class InviteParticipantsToPartyWizard(models.TransientModel):
    """ This wizard creates a new event for information party. """
    _name = 'crm.event.invite.participant.party.wizard'
    _description = 'Invite event participants to party wizard'

    registration_ids = fields.Many2many(
        'event.registration', 'event_registration_to_party_invitation_rel',
        string='Choose participants',
        default=lambda s: s._default_registration_ids()
    )
    event_id = fields.Many2one(
        'event.event', default=lambda s: s.env.context.get('active_id')
    )
    date_start = fields.Datetime(required=True)
    date_end = fields.Datetime(required=True)
    address_id = fields.Many2one(
        'res.partner', 'Location',
        default=lambda s: s.env.user.company_id.partner_id.id)

    @api.multi
    def _default_registration_ids(self):
        return self.env['event.registration'].search([
            ('event_id', '=', self.env.context.get('active_id')),
            ('state', '=', 'open')
        ])

    @api.multi
    def open_event(self):
        event = self.env['event.event'].browse(
            self.env.context.get('active_id'))
        config = self.env.ref(
            'website_event_compassion.group_visit_information_day_config')
        name = ' - Information Party'
        if event.state == 'done':
            # Use the after trip party invitation template
            config = self.env.ref(
                'website_event_compassion.group_visit_after_party_config')
            name = ' - After Party'
        party_event = self.env['event.event'].create({
            'name': event.name + name,
            'event_type_id': self.env.ref(
                'website_event_compassion.event_type_meeting').id,
            'user_id': self.env.uid,
            'date_begin': self.date_start,
            'date_end': self.date_end,
            'event_mail_ids': [(0, 0, {
                'communication_id': config.id,
                'interval_type': 'after_sub',
                'interval_nbr': '1',
                'interval_unit': 'hours'
            })],
            'event_ticket_ids': False,
            'compassion_event_id': event.compassion_event_id.id,
            'address_id': self.address_id.id,
        })
        for registration in self.registration_ids:
            registration.copy({
                'event_id': party_event.id,
            })
        return {
            'name': 'Event',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'event.event',
            'res_id': party_event.id,
            'context': self.env.context,
            'target': 'current',
        }
