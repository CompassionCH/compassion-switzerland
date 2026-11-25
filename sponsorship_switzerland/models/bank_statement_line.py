##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models

# QR reference types whose digits 23-26 are a fund id: 6 fund, 7 fund campaign
FUND_TYPES = ("6", "7")


class BankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def _get_qr_product(self):
        """T3622 Fund donations are no longer invoiced. Their QR reference is
        9 digits + partner ref (7) + 5 digits + type 6 (fund) or 7 (fund
        campaign) + fund id (4) + check digit (see Code_ref_QR (BVR) and
        res.partner.generate_bvr_reference). The reconcile rule with these
        types books the payment on the fund product.
        """
        product = super()._get_qr_product()
        reference = self._get_qr_reference()
        if product or not reference or reference[21] not in FUND_TYPES:
            return product
        fund_id = int(reference[22:26])
        if not fund_id or self._is_sponsorship_reference(reference):
            return product
        return product.search([("fund_id", "=", fund_id)], limit=1)

    def _is_sponsorship_reference(self, reference):
        """Old sponsorship payment groups have references that look like fund
        references (e.g. type 7 + 0105). A payment with the reference of a
        group or of an open invoice is never a fund donation."""
        if self.env["recurring.contract.group"].search_count(
            [
                ("bvr_reference", "=", reference),
                ("company_id", "=", self.company_id.id),
            ],
            limit=1,
        ):
            return True
        return bool(
            self.env["account.move"].search_count(
                [
                    ("payment_reference", "=", reference),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "in", ("not_paid", "partial")),
                    ("company_id", "=", self.company_id.id),
                ],
                limit=1,
            )
        )
