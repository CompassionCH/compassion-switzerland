##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models


class MassMailingSubscriptionList(models.Model):
    _inherit = "mail.mass_mailing.list_contact_rel"

    @api.multi
    def write(self, vals):
        """ Push opt-out to partner """
        if "opt_out" in vals:
            self.mapped("contact_id.partner_id").write({"opt_out": vals["opt_out"]})
        return super().write(vals)
