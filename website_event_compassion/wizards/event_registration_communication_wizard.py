##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class EventRegistrationCommunicationWizard(models.TransientModel):
    _name = 'event.registration.communication.wizard'
    _description = 'wizard that will load a chosen' \
                   'config for a email to send'

    config_id = fields.Many2one(
        'partner.communication.config', 'Communication',
        domain="[('model', '=', 'event.registration')]"
    )

    @api.multi
    def button_open_mail_sender(self):
        communication = self.env['partner.communication.job'].create({
            'config_id': self.config_id.id,
            'partner_id': self.env.context['partner_id'],
            'object_ids': self.env.context['object_ids'],
            'auto_send': False
        })

        return {
            'name': communication.subject,
            'type': 'ir.actions.act_window',
            'res_model': 'partner.communication.job',
            'res_id': communication.id,
            'view_mode': 'form',
            'target': 'new'
        }
