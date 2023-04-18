##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def action_payslip_done(self):
        """Add analytic tags to salary moves."""
        res = super(HrPayslip, self).action_payslip_done()
        for slip in self:
            analytic_tag_ids = slip.contract_id.analytic_tag_id.ids
            if analytic_tag_ids:
                move = self.env["account.move"].search([("ref", "=", slip.number)])
                move.button_cancel()
                move.line_ids.filtered("analytic_account_id").write(
                    {"analytic_tag_ids": [(6, 0, analytic_tag_ids)]}
                )
                move.post()
        return res
