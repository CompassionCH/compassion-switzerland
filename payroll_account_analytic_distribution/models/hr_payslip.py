# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _prepare_debit_line(
        self, line, amount, date, debit_account_id, move_line_analytic_ids
    ):
        vals = super()._prepare_debit_line(
            line, amount, date, debit_account_id, move_line_analytic_ids
        )
        return self._apply_contract_distribution(line, vals)

    def _prepare_credit_line(
        self, line, amount, date, credit_account_id, move_line_analytic_ids
    ):
        vals = super()._prepare_credit_line(
            line, amount, date, credit_account_id, move_line_analytic_ids
        )
        return self._apply_contract_distribution(line, vals)

    def _apply_contract_distribution(self, line, vals):
        """The distribution of the contract goes on the income and expense lines
        of the payslip; the balance sheet lines get no analytic distribution."""
        distribution = line.slip_id.contract_id.analytic_distribution
        if distribution:
            account = self.env["account.account"].browse(vals["account_id"])
            income_expense = account.internal_group in ("income", "expense")
            vals["analytic_distribution"] = distribution if income_expense else False
            if income_expense:
                vals["manual_distribution_id"] = (
                    line.slip_id.contract_id.manual_distribution_id.id
                )
        return vals
