##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import Command
from odoo.tests.common import TransactionCase
from odoo.tools import mod10r


class TestStatementImportPayer(TransactionCase):
    """T3718 A sponsorship QRR reference holding the correspondent's ref
    gets the payer as partner at import, so that the invoice matching rule
    finds the payer's open invoice.
    T3724 Same for the older standing-order references, of another layout,
    through the open invoice carrying the reference."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        partner_obj = cls.env["res.partner"]
        cls.payer = partner_obj.create({"name": "T3718 Payer", "ref": "9993719"})
        cls.correspondent = partner_obj.create(
            {"name": "T3718 Correspondent", "ref": "9993718"}
        )
        cls.qrr = cls._qrr(cls.correspondent.ref, "0")
        cls.group = cls.env["recurring.contract.group"].create(
            {"partner_id": cls.payer.id, "bvr_reference": cls.qrr}
        )
        cls.env["recurring.contract"].create(
            {
                "type": "S",
                "partner_id": cls.payer.id,
                "correspondent_id": cls.correspondent.id,
                "group_id": cls.group.id,
            }
        )
        cls.journal = cls.env["account.journal"].create(
            {"name": "T3718 QRR", "type": "bank", "code": "T3718"}
        )

    @staticmethod
    def _qrr(partner_ref, ref_type):
        return mod10r(f"{partner_ref:0>16}00001{ref_type}0000")

    def _import_partner(self, payment_ref, ref=None):
        """Partner set on the line by the statement import, camt54 having
        set the one of the partner ref inside the QRR reference."""
        qrr = payment_ref if ref is None else ref
        transaction = {
            "payment_ref": payment_ref,
            "amount": 42.0,
            "date": "2026-11-23",
            # camt54 reads digits 10-16 (qrr_partner_ref = 10,7)
            "partner_ref": qrr[9:16].lstrip("0"),
        }
        if ref:
            transaction["ref"] = ref
        stmts_vals = self.env["account.statement.import"]._complete_stmts_vals(
            [{"transactions": [transaction]}], self.journal, False
        )
        partner_id = stmts_vals[0]["transactions"][0].get("partner_id")
        return self.env["res.partner"].browse(partner_id)

    def _payer_invoice(self, payer=None, qrr=None):
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": (payer or self.payer).id,
                "payment_reference": qrr or self.qrr,
                "invoice_line_ids": [
                    Command.create({"name": "Sponsorship", "price_unit": 42.0})
                ],
            }
        )
        invoice.action_post()
        return invoice

    def test_group_payer(self):
        self.assertEqual(self._import_partner(self.qrr), self.payer)

    def test_qrr_in_move_ref(self):
        # The bank puts the reference in the ref when the donor wrote a message
        partner = self._import_partner("Happy Christmas", ref=self.qrr)
        self.assertEqual(partner, self.payer)

    def test_group_without_sponsorship_ignored(self):
        # Former group of the correspondent sharing the same reference
        self.env["recurring.contract.group"].create(
            {"partner_id": self.correspondent.id, "bvr_reference": self.qrr}
        )
        self.assertEqual(self._import_partner(self.qrr), self.payer)

    def test_invoice_payer_before_group_payer(self):
        # Another group can share the reference: the open invoice tells who pays
        other_payer = self.env["res.partner"].create({"name": "T3718 Other payer"})
        self._payer_invoice(other_payer)
        self.assertEqual(self._import_partner(self.qrr), other_payer)

    def test_invoice_payer_matched_by_rule(self):
        invoice = self._payer_invoice()
        partner = self._import_partner(self.qrr)
        self.assertEqual(partner, self.payer)
        self.assertEqual(self._rule_proposal(self.qrr, partner), invoice)

    def _rule_proposal(self, qrr, partner):
        """Invoice proposed by the invoice matching rule for a line paid
        with this reference, with the partner set at import."""
        st_line = self.env["account.bank.statement.line"].create(
            {
                "journal_id": self.journal.id,
                "date": "2026-11-23",
                "amount": 42.0,
                "payment_ref": qrr,
                "partner_id": partner.id,
            }
        )
        rule = self.env["account.reconcile.model"].create(
            {
                "name": f"T3718 invoice matching {qrr}",
                "rule_type": "invoice_matching",
                "match_partner": True,
                "match_text_location_label": True,
                "match_journal_ids": [Command.set(self.journal.ids)],
            }
        )
        result = rule._apply_rules(st_line, st_line._retrieve_partner())
        return result.get("amls", self.env["account.move.line"]).move_id

    def test_gift_reference_unchanged(self):
        gift_qrr = self._qrr(self.correspondent.ref, "4")
        self.assertEqual(self._import_partner(gift_qrr), self.correspondent)

    def test_unknown_reference_unchanged(self):
        self.group.bvr_reference = False
        self.assertEqual(self._import_partner(self.qrr), self.correspondent)

    # T3724 Older standing-order references
    @staticmethod
    def _old_qrr(digits):
        """Older standing-order reference: no partner ref in digits 10-16,
        the 22nd digit is not a reference type."""
        return mod10r(digits)

    def test_old_reference_invoice_payer(self):
        # Digits 10-16 are nobody's ref: camt54 sets no partner
        old_qrr = self._old_qrr("12345600099937240010583821")
        self.assertFalse(self._import_partner(old_qrr))
        invoice = self._payer_invoice(qrr=old_qrr)
        partner = self._import_partner(old_qrr)
        self.assertEqual(partner, self.payer)
        self.assertEqual(self._rule_proposal(old_qrr, partner), invoice)

    def test_old_reference_in_move_ref(self):
        old_qrr = self._old_qrr("12345600099937240010583821")
        self._payer_invoice(qrr=old_qrr)
        partner = self._import_partner("Happy Christmas", ref=old_qrr)
        self.assertEqual(partner, self.payer)

    def test_old_reference_other_partner_digits(self):
        # Digits 10-16 are the ref of an unrelated partner
        old_qrr = self._old_qrr(f"000000000{self.correspondent.ref}4711230510")
        self.assertEqual(self._import_partner(old_qrr), self.correspondent)
        invoice = self._payer_invoice(qrr=old_qrr)
        partner = self._import_partner(old_qrr)
        self.assertEqual(partner, self.payer)
        self.assertEqual(self._rule_proposal(old_qrr, partner), invoice)

    def test_old_reference_like_gift_or_fund(self):
        # Older references can look like today's gift or fund references:
        # the open invoice carrying them tells they are sponsorships
        for old_qrr in (
            self._qrr(self.correspondent.ref, "3"),
            mod10r(f"{self.correspondent.ref:0>16}0000060105"),
        ):
            with self.subTest(old_qrr=old_qrr):
                invoice = self._payer_invoice(qrr=old_qrr)
                partner = self._import_partner(old_qrr)
                self.assertEqual(partner, self.payer)
                self.assertEqual(self._rule_proposal(old_qrr, partner), invoice)

    def test_fund_reference_unchanged(self):
        fund_qrr = mod10r(f"{self.correspondent.ref:0>16}0000060105")
        self.assertEqual(self._import_partner(fund_qrr), self.correspondent)

    def test_old_reference_several_payers_unchanged(self):
        old_qrr = self._old_qrr(f"000000000{self.correspondent.ref}4711230510")
        self._payer_invoice(qrr=old_qrr)
        self._payer_invoice(
            self.env["res.partner"].create({"name": "T3724 Other"}), old_qrr
        )
        self.assertEqual(self._import_partner(old_qrr), self.correspondent)

    def test_old_reference_contacts_of_one_payer(self):
        # Invoices of a company and of its contact: one payer, the company
        contact = self.env["res.partner"].create(
            {"name": "T3724 Contact", "parent_id": self.payer.id}
        )
        old_qrr = self._old_qrr("12345600099937240010583821")
        self._payer_invoice(qrr=old_qrr)
        self._payer_invoice(contact, old_qrr)
        self.assertEqual(self._import_partner(old_qrr), self.payer)

    def test_old_reference_draft_invoice_unchanged(self):
        old_qrr = self._old_qrr(f"000000000{self.correspondent.ref}4711230510")
        self._payer_invoice(qrr=old_qrr).button_draft()
        self.assertEqual(self._import_partner(old_qrr), self.correspondent)

    def test_wrong_check_digit_unchanged(self):
        old_qrr = self._old_qrr(f"000000000{self.correspondent.ref}4711230510")
        self._payer_invoice(qrr=old_qrr)
        wrong = old_qrr[:-1] + str((int(old_qrr[-1]) + 1) % 10)
        self.assertEqual(self._import_partner(wrong), self.correspondent)
