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
    product_id = fields.Many2one('product.product', 'Registration product',
                                 domain=[('event_ok', '=', True)])
    seats_min = fields.Integer('Minimum participants required')
    seats_max = fields.Integer('Maximum participants allowed')
    fundraising = fields.Boolean()
    donation_product_id = fields.Many2one(
        'product.product', 'Donation product')
    participants_amount_objective = fields.Integer(
        'Default raise objective by participant', default=10000)
    sponsorship_donation_value = fields.Float(
        'Sponsorship to CHF donation conversion',
        default=1000,
        help='This sets how much the barometer of the participant will be '
             'raised when a sponsorship is made for him.'
    )
    custom_amount_objective = fields.Boolean(
        'Participant can set his fundraising objective'
    )

    @api.multi
    def open_event(self):
        event = self.env['crm.event.compassion'].browse(
            self.env.context.get('active_id'))
        odoo_event = self.env['event.event'].create({
            'name': event.name,
            'event_type_id': event.event_type_id.id,
            'user_id': self.env.uid,
            'date_begin': event.start_date,
            'date_end': event.end_date,
            'seats_min': self.seats_min,
            'seats_max': self.seats_max,
            'seats_availability': self.seats_max and 'limited' or 'unlimited',
            'compassion_event_id': event.id,
            'participants_amount_objective':
            self.participants_amount_objective,
            'custom_amount_objective': self.custom_amount_objective,
            'fundraising': self.fundraising,
            'donation_product_id': self.donation_product_id.id,
            'sponsorship_donation_value': self.sponsorship_donation_value,
        })
        odoo_event.event_ticket_ids[:1].write({
            'price': self.registration_fee,
            'product_id': self.product_id.id,
        })
        event.odoo_event_id = odoo_event
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
