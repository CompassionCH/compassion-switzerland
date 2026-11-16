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
        partner = self.employee_id._get_accounting_partner()
        vals["partner_id"] = partner.id
        vals["commercial_partner_id"] = partner.commercial_partner_id.id
        return vals

    def _get_expense_account_destination(self):
        private = self.employee_id.sudo().private_partner_id
        if self.payment_mode == "company_account" or not private:
            return super()._get_expense_account_destination()
        account = private.with_company(self.company_id).property_account_payable_id
        return account.id or super()._get_expense_account_destination()
