##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import Command
from odoo.tests.common import TransactionCase


class TestFundReconcile(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.income_account = cls.env["account.account"].create(
            {
                "code": "T3622.1",
                "name": "Christmas fund income",
                "account_type": "income",
            }
        )
        cls.button_account = cls.env["account.account"].create(
            {
                "code": "T3622.2",
                "name": "Christmas fund button",
                "account_type": "income",
            }
        )
        cls.product = cls._create_fund_product("Christmas fund", 3622)
        cls.product.property_account_income_id = cls.income_account
        cls.partner = cls.env["res.partner"].create({"name": "Fund donor"})
        cls.journal = cls.env["account.journal"].create(
            {"name": "Test QRR", "type": "bank", "code": "T3622"}
        )
        cls.no_model = cls.env["account.reconcile.model"]

    @classmethod
    def _create_fund_product(cls, name, fund_id):
        product = cls.env["product.product"].create({"name": name})
        product.product_tmpl_id.fund_id = fund_id
        return product

    def _fund_ref(self, product=None):
        return self.partner.generate_bvr_reference(product or self.product)

    def _create_line(self, ref, partner=True, amount=50.0):
        return self.env["account.bank.statement.line"].create(
            {
                "journal_id": self.journal.id,
                "date": "2026-12-01",
                "payment_ref": ref,
                "amount": amount,
                "partner_id": self.partner.id if partner else False,
            }
        )

    def _income_lines(self, line, account):
        return line.move_id.line_ids.filtered(lambda ml: ml.account_id == account)

    def test_fund_product_from_payment_ref(self):
        line = self._create_line(self._fund_ref())
        self.assertEqual(line._get_fund_product(), self.product)

    def test_fund_product_from_move_ref(self):
        line = self._create_line("Merry Christmas")
        line.ref = self._fund_ref()
        self.assertEqual(line._get_fund_product(), self.product)

    def test_fund_product_ignores_gift_reference(self):
        # Gift type 4 followed by 0000
        line = self._create_line("0000000001234000014" + "0000" + "0")
        self.assertFalse(line._get_fund_product())

    def test_fund_product_unknown_fund(self):
        other = self._create_fund_product("Other fund", 3623)
        ref = self._fund_ref(other)
        other.unlink()
        self.assertFalse(self._create_line(ref)._get_fund_product())

    def test_auto_reconcile_with_income_account(self):
        line = self._create_line(self._fund_ref())
        line._do_auto_reconcile(self.no_model)
        self.assertTrue(line.is_reconciled)
        income = self._income_lines(line, self.income_account)
        self.assertEqual(len(income), 1)
        self.assertEqual(income.credit, 50.0)
        self.assertEqual(income.product_id, self.product)
        self.assertEqual(income.partner_id, self.partner)

    def test_auto_reconcile_prefers_writeoff_button(self):
        button = self.env["account.reconcile.model"].create(
            {
                "name": "Christmas fund button",
                "rule_type": "writeoff_button",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.button_account.id,
                            "product_id": self.product.id,
                        }
                    )
                ],
            }
        )
        line = self._create_line(self._fund_ref())
        line._do_auto_reconcile(self.no_model)
        self.assertTrue(line.is_reconciled)
        booked = self._income_lines(line, self.button_account)
        self.assertEqual(booked.reconcile_model_id, button)
        self.assertFalse(self._income_lines(line, self.income_account))

    def test_no_auto_reconcile_without_partner(self):
        line = self._create_line(self._fund_ref(), partner=False)
        line._do_auto_reconcile(self.no_model)
        self.assertFalse(line.is_reconciled)

    def test_no_auto_reconcile_for_other_reference(self):
        line = self._create_line("Some donation")
        line._do_auto_reconcile(self.no_model)
        self.assertFalse(line.is_reconciled)
