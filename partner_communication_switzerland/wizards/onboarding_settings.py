##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class DemandPlanningSettings(models.TransientModel):
    _inherit = "res.config.settings"

    new_donors_user = fields.Many2one(
        "res.users", "User to notify on new donors onboarding opt out", readonly=False
    )

    @api.multi
    def set_values(self):
        super().set_values()
        self.env["ir.config_parameter"].set_param(
            "partner_communication_switzerland.new_donors_user",
            str(self.new_donors_user.id or 0),
        )

    @api.model
    def get_values(self):
        res = super().get_values()
        param_obj = self.env["ir.config_parameter"].sudo()
        new_donors_user_id = int(
            param_obj.get_param(
                "partner_communication_switzerland.new_donors_user", "0"
            )
        )
        res.update(
            {
                "new_donors_user": new_donors_user_id,
            }
        )
        return res
