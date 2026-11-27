##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo import models
from odoo.tools import mod10r

# QR (BVR) reference: 26 digits + check digit
QRR = re.compile(r"\d{27}")
# Sponsorship QRR reference: 9 digits + partner ref (7) + group counter (5)
# + type 0 + 0000 + check digit (see recurring.contract.group
# compute_partner_bvr_ref). Gift (1-6) and fund (6 + fund id) references
# don't match.
SPONSORSHIP_QRR = re.compile(r"\d{21}0\d{5}")


class AccountStatementImport(models.TransientModel):
    _inherit = "account.statement.import"

    def _complete_stmts_vals(self, stmts_vals, journal, account_number):
        """T3718 A sponsorship QRR reference is the reference of the payment
        group. The partner ref inside it is the one of the partner the group
        was first made for (e.g. the correspondent, or a former sponsor), not
        always the payer, but camt54 sets the partner from it. Set the payer
        instead, so that the invoice matching rule finds the open invoices.
        T3724 Older standing orders pay with a QRR reference of another
        layout, with no partner ref inside: the open invoices carrying it
        tell the payer."""
        stmts_vals = super()._complete_stmts_vals(stmts_vals, journal, account_number)
        company = journal.company_id or self.env.company
        for st_vals in stmts_vals:
            for line_vals in st_vals["transactions"]:
                payer = self._get_sponsorship_payer(line_vals, company)
                if payer:
                    line_vals["partner_id"] = payer.id
        return stmts_vals

    def _get_sponsorship_payer(self, line_vals, company):
        """Payer of the open invoices carrying the QRR reference of the line,
        whatever its layout, or else, for a sponsorship reference, of the
        sponsorship group. The bank puts the reference in the label, or in
        the reference when the donor wrote a message.
        A gift or fund reference has no open invoice: it keeps its partner,
        and its QR reconcile rule decodes it.
        :return: res.partner, empty if not found or not unique
        """
        partner_obj = self.env["res.partner"]
        for ref in (line_vals.get("payment_ref"), line_vals.get("ref")):
            ref = (ref or "").strip()
            if not QRR.fullmatch(ref) or mod10r(ref[:-1]) != ref:
                continue
            invoices = self.env["account.move"].search(
                [
                    ("payment_reference", "=", ref),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "in", ("not_paid", "partial")),
                    ("company_id", "=", company.id),
                ]
            )
            payer = invoices.mapped("partner_id.commercial_partner_id")
            if not payer and SPONSORSHIP_QRR.fullmatch(ref):
                groups = (
                    self.env["recurring.contract.group"]
                    .search(
                        [
                            ("bvr_reference", "=", ref),
                            ("company_id", "=", company.id),
                        ]
                    )
                    .filtered("contains_sponsorship")
                )
                payer = groups.mapped("partner_id.commercial_partner_id")
            return payer if len(payer) == 1 else partner_obj
        return partner_obj
