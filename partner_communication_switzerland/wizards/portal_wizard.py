##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    invitation_config_id = fields.Many2one('partner.communication.config')

    @api.onchange('portal_id')
    def onchange_portal_id(self):
        # set the values of the users created in the super method
        res = super().onchange_portal_id()

        self.user_ids.write({
            'invitation_config_id': self.invitation_config_id.id
        })

        return res


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    invitation_config_id = fields.Many2one('partner.communication.config')
    uid_communication_id = fields.Many2one('partner.communication.job')

    @api.multi
    def action_apply(self):
        res = super().action_apply()

        self.mapped('partner_id').sudo().signup_prepare()

        if self.env.context.get('create_communication'):
            for wizard_line in self:
                wizard_line.create_uid_communication()

        return res

    @api.multi
    def create_uid_communication(self):
        """create a communication that contain a login url"""
        if not self.env.user.email:
            raise UserError(_('You must have an email address in'
                              ' your User Preferences to send emails.'))
        self.ensure_one()

        self.uid_communication_id = \
            self.env['partner.communication.job'].create({
                'partner_id': self.user_id.partner_id.id,
                'object_ids': self.user_id.id,
                'config_id': self.invitation_config_id.id
            })
