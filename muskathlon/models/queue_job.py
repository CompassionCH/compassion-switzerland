##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, _


class QueueJob(models.Model):
    _inherit = 'queue.job'

    @api.multi
    def related_action_registration(self):
        registration_id = self.record_ids[0]
        action = {
            'name': _("Muskathlon registration"),
            'type': 'ir.actions.act_window',
            'res_model': 'event.registration',
            'res_id': registration_id,
            'view_type': 'form',
            'view_mode': 'form',
        }
        return action

    @api.multi
    def related_action_partner(self):
        partner_id = self.record_ids[0]
        action = {
            'name': _("Partner"),
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': partner_id,
            'view_type': 'form',
            'view_mode': 'form',
        }
        return action
