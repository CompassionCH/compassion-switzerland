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
from odoo.tools import mod10r


class TestFundReconcile(TransactionCase):
    """T3622 A QR payment first pays the open invoice of exactly its reference
    and amount; only then the QR reference rule books it on the fund."""

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
        cls.partner = cls.env["res.partner"].create(
            {"name": "Fund donor", "ref": "9993622"}
        )
        cls.journal = cls.env["account.journal"].create(
            {"name": "Test QRR", "type": "bank", "code": "T3622"}
        )
        model_obj = cls.env["account.reconcile.model"]
        cls.invoice_rule = model_obj.create(
            {
                "name": "T3622 invoice matching",
                "rule_type": "invoice_matching",
                "auto_reconcile": True,
                "match_partner": True,
                "match_text_location_label": True,
                "match_text_location_reference": True,
                "match_exact_reference": True,
                "exact_amount_only": True,
                "past_months_limit": 0,
                "sequence": 1,
                "company_id": cls.company.id,
            }
        )
        cls.fund_rule = model_obj.create(
            {
                "name": "T3622 funds and campaigns",
                "rule_type": "writeoff_suggestion",
                "auto_reconcile": True,
                "match_partner": True,
                "sequence": 2,
                "company_id": cls.company.id,
                "qr_type_ids": [
                    Command.set(
                        [
                            cls.env.ref("account_reconcile_compassion_ce.qr_type_6").id,
                            cls.env.ref("account_reconcile_compassion_ce.qr_type_7").id,
                        ]
                    )
                ],
            }
        )
        cls.rules = cls.invoice_rule | cls.fund_rule

    @classmethod
    def _create_fund_product(cls, name, fund_id):
        product = cls.env["product.product"].create({"name": name})
        product.product_tmpl_id.fund_id = fund_id
        return product

    def _fund_ref(self, product=None):
        return self.partner.generate_bvr_reference(product or self.product)

    def _legacy_group_ref(self):
        """Old sponsorship group reference that looks like a fund reference:
        group counter 01506, type 7, fund id of the test product"""
        return mod10r(f"{self.partner.ref:0>16}015067{self.product.fund_id:0>4}")

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

    def _reconcile(self, line):
        if not line.is_reconciled:
            line._do_auto_reconcile(self.rules)
        return line

    def _open_invoice(self, ref, amount=50.0):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": "2026-12-01",
                "payment_reference": ref,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Sponsorship",
                            "price_unit": amount,
                            "account_id": self.income_account.id,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def _income_lines(self, line, account):
        return line.move_id.line_ids.filtered(lambda ml: ml.account_id == account)

    def test_fund_product_from_payment_ref(self):
        line = self._create_line(self._fund_ref())
        self.assertEqual(line._get_qr_product(), self.product)

    def test_fund_product_from_move_ref(self):
        line = self._create_line("Merry Christmas")
        line.ref = self._fund_ref()
        self.assertEqual(line._get_qr_product(), self.product)

    def test_fund_product_ignores_gift_reference(self):
        # Gift type 4 followed by 0000
        line = self._create_line(mod10r(f"{self.partner.ref:0>16}0001440000"))
        self.assertFalse(line._get_qr_product())

    def test_fund_product_unknown_fund(self):
        other = self._create_fund_product("Other fund", 3623)
        ref = self._fund_ref(other)
        other.unlink()
        self.assertFalse(self._create_line(ref)._get_qr_product())

    def test_fund_product_wrong_check_digit(self):
        ref = self._fund_ref()
        ref = ref[:-1] + str((int(ref[-1]) + 1) % 10)
        self.assertFalse(self._create_line(ref)._get_qr_product())

    def test_auto_reconcile_with_income_account(self):
        line = self._reconcile(self._create_line(self._fund_ref()))
        self.assertTrue(line.is_reconciled)
        income = self._income_lines(line, self.income_account)
        self.assertEqual(len(income), 1)
        self.assertEqual(income.credit, 50.0)
        self.assertEqual(income.product_id, self.product)
        self.assertEqual(income.partner_id, self.partner)
        self.assertEqual(income.reconcile_model_id, self.fund_rule)

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
        line = self._reconcile(self._create_line(self._fund_ref()))
        self.assertTrue(line.is_reconciled)
        booked = self._income_lines(line, self.button_account)
        self.assertEqual(booked.reconcile_model_id, button)
        self.assertFalse(self._income_lines(line, self.income_account))

    def test_no_auto_reconcile_without_partner(self):
        line = self._reconcile(self._create_line(self._fund_ref(), partner=False))
        self.assertFalse(line.is_reconciled)

    def test_no_auto_reconcile_for_unknown_partner_ref(self):
        ref = mod10r(f"{'1':0>16}000006{self.product.fund_id:0>4}")
        line = self._reconcile(self._create_line(ref))
        self.assertFalse(line.is_reconciled)

    def test_no_auto_reconcile_for_other_reference(self):
        line = self._reconcile(self._create_line("Some donation"))
        self.assertFalse(line.is_reconciled)

    def test_open_invoice_same_reference_and_amount(self):
        """Fund-like reference of an old sponsorship group: the open invoice is
        paid, no fund donation is booked"""
        ref = self._legacy_group_ref()
        invoice = self._open_invoice(ref, 84.0)
        line = self._reconcile(self._create_line(ref, amount=84.0))
        self.assertTrue(line.is_reconciled)
        self.assertEqual(invoice.payment_state, "paid")
        self.assertFalse(line.move_id.line_ids.product_id)

    def test_open_invoice_several_months(self):
        """A payment of two open months of the reference pays both"""
        ref = self._legacy_group_ref()
        invoices = self._open_invoice(ref, 84.0) | self._open_invoice(ref, 84.0)
        line = self._reconcile(self._create_line(ref, amount=168.0))
        self.assertTrue(line.is_reconciled)
        self.assertEqual(set(invoices.mapped("payment_state")), {"paid"})

    def test_open_invoice_other_amount(self):
        """Not the invoiced amount: left to the accountant, never a fund"""
        ref = self._legacy_group_ref()
        invoice = self._open_invoice(ref, 84.0)
        line = self._reconcile(self._create_line(ref, amount=100.0))
        self.assertFalse(line.is_reconciled)
        self.assertEqual(invoice.payment_state, "not_paid")
        self.assertFalse(line._get_qr_product())

    def test_group_reference_without_invoice(self):
        """Reference of a payment group: never a fund donation"""
        ref = self._legacy_group_ref()
        self.env["recurring.contract.group"].create(
            {"partner_id": self.partner.id, "bvr_reference": ref}
        )
        line = self._reconcile(self._create_line(ref))
        self.assertFalse(line.is_reconciled)
        self.assertFalse(line._get_qr_product())

    def test_fund_reference_paid_invoice_books_fund(self):
        """A former invoice of the reference (paid, as v14 made for every fund
        donation) doesn't block the fund booking"""
        invoice = self._open_invoice(self._fund_ref())
        invoice.button_draft()
        invoice.button_cancel()
        line = self._reconcile(self._create_line(self._fund_ref()))
        self.assertTrue(line.is_reconciled)
        self.assertTrue(self._income_lines(line, self.income_account))

    def test_module_rules(self):
        """The rules shipped by the module decode funds/campaigns (automatic)
        and gifts (manual)"""
        funds = self.env.ref("sponsorship_switzerland.reconcile_model_qr_funds")
        gifts = self.env.ref("sponsorship_switzerland.reconcile_model_qr_gifts")
        self.assertTrue(funds.auto_reconcile)
        self.assertFalse(gifts.auto_reconcile)
        self.assertEqual(sorted(funds.qr_type_ids.mapped("code")), ["6", "7"])
        self.assertEqual(
            sorted(gifts.qr_type_ids.mapped("code")), ["1", "2", "3", "4", "5"]
        )
