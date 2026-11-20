##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import date

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProvision(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provision_rule = cls.env.ref("hr_switzerland_13th_salary.PROVISION_13")
        cls.clear_rule = cls.env["hr.salary.rule"].create(
            {"name": "Clear provision 13 test", "code": "CLEAR_PROVISION_13"}
        )
        cls.employee = cls.env["hr.employee"].create({"name": "Provision test A"})
        cls.other = cls.env["hr.employee"].create({"name": "Provision test B"})
        cls.contract = cls._contract(cls.employee)
        cls.other_contract = cls._contract(cls.other)

    @classmethod
    def _contract(cls, employee):
        return cls.env["hr.contract"].create(
            {"name": "Provision test", "employee_id": employee.id, "wage": 1000}
        )

    def _slip(self, contract, month, provision, clear=0, state="done", **vals):
        lines = [(self.provision_rule, provision)]
        if clear:
            lines.append((self.clear_rule, clear))
        return self.env["hr.payslip"].create(
            {
                "employee_id": contract.employee_id.id,
                "contract_id": contract.id,
                "date_from": date(2026, month, 1),
                "date_to": date(2026, month, 28),
                "state": state,
                "line_ids": [
                    Command.create(
                        {
                            "name": rule.name,
                            "code": rule.code,
                            "salary_rule_id": rule.id,
                            "employee_id": contract.employee_id.id,
                            "contract_id": contract.id,
                            "amount": amount,
                        }
                    )
                    for rule, amount in lines
                ],
                **vals,
            }
        )

    def test_provision_of_the_half_year(self):
        # First half-year, paid in June: nothing left
        self._slip(self.contract, 5, 100)
        self._slip(self.contract, 6, 100, clear=200)
        # Second half-year
        self._slip(self.contract, 7, 100)
        self._slip(self.contract, 8, 100)
        self._slip(self.contract, 9, 100, state="draft")  # not done
        self._slip(self.contract, 9, 30, credit_note=True)  # refund
        self._slip(self.other_contract, 8, 500)  # another employee
        provision = self.contract._get_13_salary_provision
        self.assertEqual(provision(date(2026, 6, 1)), 100)
        self.assertEqual(provision(date(2026, 6, 30)), 0)
        self.assertEqual(provision(date(2026, 12, 31)), 170)
        self.assertEqual(provision(date(2026, 8, 1)), 100)

    def test_amount_on_the_payslip(self):
        self._slip(self.contract, 7, 100)
        self._slip(self.contract, 8, 100)
        slip = self._slip(self.contract, 9, 0, state="draft")
        self.assertEqual(slip.amount_13_salary, 0)
        slip.pay_13_salary = True
        self.assertEqual(slip.amount_13_salary, 200)
        # Paid in the half-year (e.g. employee leaving): nothing left after
        self._slip(self.contract, 9, 100, clear=300)
        slip = self._slip(self.contract, 10, 0, state="draft", pay_13_salary=True)
        self.assertEqual(slip.amount_13_salary, 0)
