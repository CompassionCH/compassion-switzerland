##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    """Override of the paid module payment_postfinance_flex, which must not be
    modified directly (proprietary licence)."""

    _inherit = "payment.acquirer"

    def postfinance_form_generate_values(self, tx_values):
        """Mark the transaction as pending before the donor leaves for the gateway.

        The paid module only moves a transaction out of 'draft' when the gateway
        answers back, and by then it reports FULFILL, which takes its own branch -
        so 'pending' was never set. Odoo keys every "a payment has been initiated"
        protection on ('pending', 'authorized', 'done'), and get_last_transaction()
        drops draft records entirely, so the cart stayed editable for the whole
        payment and an already-paid order could still be emptied (T3378).

        Core calls this from render(), right after the transaction is created and
        just before the redirect, which is the last point we control on our side.
        """
        res = super().postfinance_form_generate_values(tx_values)
        # Not _set_transaction_pending(): sale's override of it emails an order
        # confirmation to the donor on every Pay click.
        self.env["payment.transaction"].search(
            [("reference", "=", tx_values.get("reference")), ("state", "=", "draft")]
        ).write({"state": "pending"})
        return res

    def cron_update_postfinance_state(self, limit=200, days=30):
        """Replaces the paid module implementation, which scanned every
        PostFinance transaction ever created, made one API call per record with
        no limit, and never committed - so a run killed by the cron timeout
        threw away all its work and started over from scratch next time.
        """
        cutoff = fields.Datetime.subtract(fields.Datetime.now(), days=days)
        transactions = self.env["payment.transaction"].search(
            [
                ("acquirer_id.provider", "=", "postfinance"),
                ("acquirer_reference", "!=", False),
                ("create_date", ">=", cutoff),
                "|",
                (
                    "postfinance_state",
                    "not in",
                    ["FULFILL", "DECLINE", "FAILED"],
                ),
                ("state", "not in", ["done", "cancel", "error"]),
            ],
            order="create_date asc",
            limit=limit,
        )
        for tx in transactions:
            try:
                _logger.info("PostFinance cron: updating transaction %s", tx.id)
                tx._postfinance_form_validate(data={})
                if tx.state == "done" and not tx.is_processed:
                    tx._post_process_after_done()
                # _postfinance_form_validate locks the row with FOR UPDATE NOWAIT.
                # Commit per transaction so progress survives a cron timeout and
                # the lock is not held for the whole run.
                self.env.cr.commit()  # pylint: disable=invalid-commit
            except Exception:
                self.env.cr.rollback()
                _logger.exception(
                    "Error while updating PostFinance transaction %s", tx.id
                )
