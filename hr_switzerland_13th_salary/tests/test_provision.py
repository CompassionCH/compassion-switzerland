##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestProvision(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.provision_account = cls.env["account.account"].create(
            {
                "name": "13th salary provision test",
                "code": "229199",
                "account_type": "liability_current",
            }
        )
        cls.env.ref(
            "hr_switzerland_13th_salary.PROVISION_13"
        ).account_credit = cls.provision_account
        cls.other_account = cls.env["account.account"].create(
            {"name": "Salaries test", "code": "400098", "account_type": "expense"}
        )
        cls.journal = cls.env["account.journal"].create(
            {"name": "Provision test", "code": "TPRV", "type": "general"}
        )
        cls.with_contact = cls.env["hr.employee"].create({"name": "Provision test A"})
        cls.without_contact = cls.env["hr.employee"].create(
            {"name": "Provision test B"}
        )
        cls.without_contact.work_contact_id = False

    def _entry(self, amount, partner=False):
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "journal_id": self.journal.id,
                "date": date(2026, 10, 31),
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "account_id": self.provision_account.id,
                            "partner_id": partner and partner.id,
                            "credit": amount,
                        },
                    ),
                    (0, 0, {"account_id": self.other_account.id, "debit": amount}),
                ],
            }
        )
        move.action_post()

    def _contract(self, employee):
        return self.env["hr.contract"].create(
            {"name": "Provision test", "employee_id": employee.id, "wage": 1000}
        )

    def test_provision_of_the_employee_only(self):
        self._entry(100, self.with_contact.work_contact_id)
        # An entry without partner (another employee, a correction...)
        self._entry(200)
        self.assertEqual(self._contract(self.with_contact).provision_13_salary, 100)
        # No contact: the lines without partner are not the employee's
        self.assertEqual(self._contract(self.without_contact).provision_13_salary, 0)
