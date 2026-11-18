from odoo import models


class HrExpense(models.Model):
    _inherit = "hr.expense"

    def _prepare_move_lines_vals(self):
        vals = super()._prepare_move_lines_vals()
        if vals.get("partner_id"):
            vals["partner_id"] = self.employee_id._get_accounting_partner().id
        return vals


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    def _prepare_bills_vals(self):
        vals = super()._prepare_bills_vals()
        # Same partner as the bank account of the employee (private partner)
        vals["partner_id"] = self.employee_id._get_accounting_partner().id
        return vals
