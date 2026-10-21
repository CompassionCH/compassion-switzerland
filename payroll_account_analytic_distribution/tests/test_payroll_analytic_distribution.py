# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPayrollAnalyticDistribution(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.expense = cls.env["account.account"].create(
            {"name": "Salaries test", "code": "400099", "account_type": "expense"}
        )
        cls.liability = cls.env["account.account"].create(
            {
                "name": "Salaries to pay test",
                "code": "209599",
                "account_type": "liability_current",
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Salaries test",
                "code": "TSAL",
                "type": "general",
                "default_account_id": cls.liability.id,
            }
        )
        plan = cls.env["account.analytic.plan"].create({"name": "Payroll test keys"})
        account_obj = cls.env["account.analytic.account"]
        cls.adm = account_obj.create({"name": "Payroll test ADM", "plan_id": plan.id})
        cls.fund = account_obj.create(
            {"name": "Payroll test Fundraising", "plan_id": plan.id}
        )
        category = cls.env["hr.salary.rule.category"].create(
            {"name": "Payroll test basic", "code": "TBASIC"}
        )
        rule = cls.env["hr.salary.rule"].create(
            {
                "name": "Payroll test salary",
                "code": "TSALARY",
                "category_id": category.id,
                "sequence": 1,
                "amount_select": "fix",
                "amount_fix": 1000,
                "account_debit": cls.expense.id,
                "account_credit": cls.liability.id,
            }
        )
        structure = cls.env["hr.payroll.structure"].create(
            {"name": "Payroll test structure", "code": "TSTRUCT", "rule_ids": [rule.id]}
        )
        employee = cls.env["hr.employee"].create({"name": "Payroll test employee"})
        cls.contract = cls.env["hr.contract"].create(
            {
                "name": "Payroll test contract",
                "employee_id": employee.id,
                "wage": 1000,
                "struct_id": structure.id,
                "journal_id": cls.journal.id,
                "date_start": date(2026, 1, 1),
                "state": "open",
            }
        )
        cls.payslip_vals = {
            "employee_id": employee.id,
            "contract_id": cls.contract.id,
            "struct_id": structure.id,
            "journal_id": cls.journal.id,
            "date_from": date(2026, 11, 1),
            "date_to": date(2026, 11, 30),
        }

    def _confirmed_payslip(self):
        payslip = self.env["hr.payslip"].create(self.payslip_vals)
        payslip.compute_sheet()
        payslip.action_payslip_done()
        return payslip

    def test_distribution_on_expenses_only(self):
        distribution = {str(self.adm.id): 30.0, str(self.fund.id): 70.0}
        self.contract.analytic_distribution = distribution
        move = self._confirmed_payslip().move_id
        expense_line = move.line_ids.filtered(lambda ml: ml.account_id == self.expense)
        liability_line = move.line_ids.filtered(
            lambda ml: ml.account_id == self.liability
        )
        self.assertEqual(expense_line.analytic_distribution, distribution)
        self.assertFalse(liability_line.analytic_distribution)
        self.assertEqual(
            sorted(expense_line.analytic_line_ids.mapped("amount")), [-700.0, -300.0]
        )

    def test_without_distribution(self):
        self.contract.analytic_account_id = self.adm
        move = self._confirmed_payslip().move_id
        expense_line = move.line_ids.filtered(lambda ml: ml.account_id == self.expense)
        self.assertEqual(expense_line.analytic_distribution, {str(self.adm.id): 100})

    def test_quality_test(self):
        if "quality.test" not in self.env:
            self.skipTest("quality_test_compassion is not installed")
        from ..hooks import QUALITY_TEST, _create_quality_test

        self.env["quality.test"].search([("name", "=", QUALITY_TEST)]).unlink()
        _create_quality_test(self.env)
        _create_quality_test(self.env)
        test = self.env["quality.test"].search([("name", "=", QUALITY_TEST)])
        self.assertEqual(len(test), 1)
        self.assertTrue(test.rule_module_update)
        self.assertIn("payroll_account", test.module_ids.mapped("name"))

    def test_key_change_goes_to_contracts(self):
        key = self.env["account.analytic.distribution.manual"].create(
            {
                "name": "Payroll test key",
                "analytic_distribution": {str(self.adm.id): 100},
            }
        )
        self.contract.write(
            {
                "manual_distribution_id": key.id,
                "analytic_distribution": key.analytic_distribution,
            }
        )
        new = {str(self.adm.id): 40.0, str(self.fund.id): 60.0}
        key.analytic_distribution = new
        self.assertEqual(self.contract.analytic_distribution, new)
        move = self._confirmed_payslip().move_id
        expense_line = move.line_ids.filtered(lambda ml: ml.account_id == self.expense)
        self.assertEqual(expense_line.analytic_distribution, new)
        self.assertEqual(expense_line.manual_distribution_id, key)
