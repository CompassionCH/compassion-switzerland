# -*- coding: utf-8 -*-
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
from odoo.exceptions import UserError


class PartnerMergeWizard(models.TransientModel):
    _inherit = 'base.partner.merge.automatic.wizard'

    @api.multi
    def action_merge(self):
        """
        Allow anybody to perform the merge of partners
        Prevent geoengine bugs
        Prevent to merge sponsors
        """
        self.partner_ids.write({'geo_point': False})
        sponsorships = self.env['recurring.contract'].search([
            ('correspondant_id', 'in', self.partner_ids.ids),
            ('state', '=', 'active'),
            ('type', 'like', 'S')
        ])
        if sponsorships:
            raise UserError(_(
                "The selected partners are sponsors! "
                "Please first modify the sponsorship and don't forget "
                "to send new labels to them."
            ))
        return super(PartnerMergeWizard, self.sudo()).action_merge()
