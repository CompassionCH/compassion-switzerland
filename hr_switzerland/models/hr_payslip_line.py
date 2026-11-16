from odoo import models


class HrPayslipLine(models.Model):
    _inherit = "hr.payslip.line"

    def _get_partner_id(self, credit_account):
        # Employee accounts (see payroll_account): private partner of the employee
        partner_id = super()._get_partner_id(credit_account)
        rule = self.salary_rule_id
        account = rule.account_credit if credit_account else rule.account_debit
        if account.account_type in ("asset_receivable", "liability_current"):
            employee = self.slip_id.employee_id
            partner_id = employee._get_accounting_partner().id or partner_id
        return partner_id
