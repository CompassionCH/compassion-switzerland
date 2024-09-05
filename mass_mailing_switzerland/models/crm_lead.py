##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models

class Lead(models.Model):
    _inherit = "crm.lead"

    def _inverse_email_from(self):
        return

    @api.depends('partner_id.email')
    def _compute_email_from(self):
        return

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        self.email_from = self.partner_id.email