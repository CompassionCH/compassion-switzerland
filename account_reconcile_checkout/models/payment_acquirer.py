##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class PaymentAcquirer(models.Model):
    """Override of the paid module payment_postfinance_flex, which must not be
    modified directly (proprietary licence)."""

    _inherit = "payment.acquirer"

    def postfinance_form_generate_values(self, tx_values):
        """Mark the transaction as pending before the donor leaves for the
        gateway."""
        res = super().postfinance_form_generate_values(tx_values)
        self.env["payment.transaction"].search(
            [("reference", "=", tx_values.get("reference")), ("state", "=", "draft")]
        ).write({"state": "pending"})
        return res

    def cron_update_postfinance_state(self, limit=200):
        """Replaces the paid module implementation, which scanned every
        PostFinance transaction ever created, made one API call per record with
        no limit, and never committed - so a run killed by the cron timeout
        threw away all its work and started over from scratch next time.

        No age cutoff: a payment the gateway never resolved is precisely the one
        we have to keep asking about, and any rolling window strands it the day
        it ages out.

        Least recently checked first, because validating writes the gateway
        state back: whatever this run touches sorts last next time, so a batch
        that keeps failing cannot hold the slots and hide older payments. A
        payment nobody has looked at yet still comes before anything the
        previous run already checked.
        """
        transactions = self.env["payment.transaction"].search(
            [
                ("acquirer_id.provider", "=", "postfinance"),
                ("acquirer_reference", "!=", False),
                "|",
                (
                    "postfinance_state",
                    "not in",
                    ["FULFILL", "DECLINE", "FAILED"],
                ),
                ("state", "not in", ["done", "cancel", "error"]),
            ],
            order="write_date asc",
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
            except Exception as error:
                self.env.cr.rollback()
                _logger.exception(
                    "Error while updating PostFinance transaction %s", tx.id
                )
                # The rollback also undid the write that validating does, so the
                # record would keep its old write_date, be picked first again on
                # every run and block every other unresolved payment. Record the
                # failed attempt in its own transaction so the queue moves on.
                try:
                    tx.write(
                        {"state_message": _("PostFinance sweep failed: %s") % error}
                    )
                    self.env.cr.commit()  # pylint: disable=invalid-commit
                except Exception:
                    self.env.cr.rollback()
                    _logger.exception(
                        "Could not record the failed sweep of transaction %s", tx.id
                    )
