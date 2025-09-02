##############################################################################
#
#    Copyright (C) 2014-today Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class CheckoutAccountConfigSettings(models.TransientModel):
    """
    Add the possibility to define which account should be reconciled
    """

    _inherit = "res.config.settings"

    account_transfer_pf_checkout = fields.Many2one("account.account", readonly=False)

    @api.model
    def get_values(self):
        res = super().get_values()
        company_id = self.env.company.id
        config = self.env["ir.config_parameter"].sudo()
        res["account_transfer_checkout"] = int(
            config.get_param(f"account_transfer_pf_checkout_{company_id}", default="0")
        )
        return res

    @api.model
    def set_values(self):
        company_id = self.env.company.id
        self.env["ir.config_parameter"].set_param(
            f"account_transfer_pf_checkout_{company_id}",
            self.account_transfer_pf_checkout.id,
        )
        super().set_values()
