from odoo import Command
from odoo.tests import tagged

from odoo.addons.hr_expense.tests.common import TestExpenseCommon


@tagged("post_install", "-at_install")
class TestPrivatePartner(TestExpenseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Work contact = user partner, attached to the company (like Compassion users)
        cls.company_partner = cls.env["res.partner"].create(
            {"name": "Employer", "is_company": True}
        )
        cls.expense_user_employee.partner_id.parent_id = cls.company_partner
        cls.private_partner = cls.env["res.partner"].create({"name": "Private Home"})
        cls.expense_employee.private_partner_id = cls.private_partner

    def _post_sheet(self, payment_mode="own_account"):
        sheet = self.create_expense_report(
            {
                "expense_line_ids": [
                    Command.create(
                        {
                            "employee_id": self.expense_employee.id,
                            "product_id": self.product_c.id,
                            "total_amount_currency": 100.0,
                            "tax_ids": [Command.clear()],
                            "payment_mode": payment_mode,
                        }
                    )
                ]
            }
        )
        sheet.action_submit_sheet()
        sheet.action_approve_expense_sheets()
        sheet.action_sheet_move_post()
        return sheet

    def test_work_details_stay_professional(self):
        user_partner = self.expense_user_employee.partner_id
        self.private_partner.write(
            {"email": "home@example.com", "mobile": "+41 79 000 00 00"}
        )
        self.assertEqual(self.expense_employee.work_contact_id, user_partner)
        self.assertEqual(self.expense_employee.work_email, user_partner.email)

    def test_expense_entry_on_private_partner(self):
        sheet = self._post_sheet()
        move = sheet.account_move_ids
        self.assertEqual(move.partner_id, self.private_partner)
        self.assertEqual(move.commercial_partner_id, self.private_partner)
        self.assertEqual(move.line_ids.partner_id, self.private_partner)

    def test_expense_entry_without_private_partner(self):
        self.expense_employee.private_partner_id = False
        sheet = self._post_sheet()
        move = sheet.account_move_ids
        # Standard: user partner, booked on its commercial partner (the company)
        self.assertEqual(move.partner_id, self.expense_user_employee.partner_id)
        self.assertEqual(move.line_ids.partner_id, self.company_partner)

    def test_payslip_line_partner(self):
        def account(code, account_type):
            return self.env["account.account"].create(
                {"code": code, "name": code, "account_type": account_type}
            )

        rule = self.env["hr.salary.rule"].new(
            {
                "name": "Net",
                "code": "NETTEST",
                "account_credit": account("209901", "liability_current").id,
                "account_debit": account("509901", "expense").id,
            }
        )
        slip = self.env["hr.payslip"].new({"employee_id": self.expense_employee.id})
        line = self.env["hr.payslip.line"].new(
            {"slip_id": slip.id, "salary_rule_id": rule.id}
        )
        line.slip_id = slip
        line.salary_rule_id = rule
        self.assertEqual(
            line._get_partner_id(credit_account=True), self.private_partner.id
        )
        self.assertFalse(line._get_partner_id(credit_account=False))
        self.expense_employee.private_partner_id = False
        self.assertEqual(
            line._get_partner_id(credit_account=True),
            self.expense_user_employee.partner_id.id,
        )

    def test_work_contact_change_keeps_private_bank_account(self):
        bank = self.env["res.partner.bank"].create(
            {
                "acc_number": "CH9300762011623852957",
                "partner_id": self.private_partner.id,
                "allow_out_payment": True,
            }
        )
        self.expense_employee.bank_account_id = bank
        other = self.env["res.partner"].create({"name": "Other work contact"})
        self.expense_employee.work_contact_id = other
        self.assertEqual(bank.partner_id, self.private_partner)
        self.assertTrue(bank.allow_out_payment)
