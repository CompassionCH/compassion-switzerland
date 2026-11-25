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
        compute="_compute_13_salary",
        store=True,
    )

    @api.depends("employee_id", "pay_13_salary", "contract_id", "state", "date_from")
    def _compute_13_salary(self):
        for payslip in self:
            if payslip.state == "draft":
                if payslip.pay_13_salary:
                    # Same amount as the salary rule TOTAL_PROVISION_13
                    payslip.amount_13_salary = (
                        payslip.contract_id._get_13_salary_provision(payslip.date_from)
                        if payslip.contract_id and payslip.date_from
                        else 0
                    )
                else:
                    payslip.amount_13_salary = 0
            else:
                payslip.amount_13_salary = payslip.amount_13_salary
