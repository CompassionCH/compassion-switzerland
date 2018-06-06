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

from odoo import api, models


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    @api.multi
    def action_apply(self):
        """
        Generate communication for User invitation
        """
        res = super(PortalWizard, self).action_apply()
        comm_obj = self.env['partner.communication.job']
        config = self.env.ref(
            'partner_communication_switzerland.portal_welcome_config')
        for user in self.mapped('user_ids.user_id'):
            comm_obj.create({
                'partner_id': user.partner_id.id,
                'object_ids': user.id,
                'config_id': config.id
            })
        return res
