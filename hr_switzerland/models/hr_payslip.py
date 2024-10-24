##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: David Wulliamoz <dwulliamoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    pay_13_salary = fields.Boolean(
        string="Pay the 13th salary this month", help="Pay the provisionned 13th salary"
    )

    amount_13_salary = fields.Float(
        string="13th salary to add",
        digits="Account",
        compute="_compute_13_salary",
        store=True,
    )

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
                move.action_post()
        return res

    @api.depends("employee_id", "pay_13_salary", "contract_id", "state")
    def _compute_13_salary(self):
        for payslip in self:
            if payslip.state == "draft":
                if payslip.pay_13_salary:
                    payslip.amount_13_salary = payslip.contract_id.provision_13_salary
                else:
                    payslip.amount_13_salary = 0
            else:
                payslip.amount_13_salary = payslip.amount_13_salary
