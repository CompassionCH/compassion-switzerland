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
    def related_action_mass_mailing(self):
        self.ensure_one()
        action = {
            'name': _("Mass Mailing"),
            'type': 'ir.actions.act_window',
            'res_model': 'mail.mass_mailing',
            'view_mode': 'form',
            'res_id': self.record_ids[0],
        }
        return action

    @api.multi
    def related_action_emails(self):
        action = {
            'name': "E-mails",
            'type': 'ir.actions.act_window',
            'res_model': 'mail.mail',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.record_ids)],
        }
        return action
