##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from psycopg2 import OperationalError

from odoo import fields, models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Override of the paid module payment_postfinance_flex, which must not be
    modified directly (proprietary licence)."""

    _inherit = "payment.transaction"

    # The paid module tests these before its own 'PENDING'/'AUTHORIZED' branches,
    # so _set_transaction_pending() is never reached and the transaction stays in
    # 'draft' for the whole payment. Odoo keys its "a payment has been initiated"
    # protections on ('pending', 'authorized', 'done'), so none of them fire: the
    # cart stays mutable and every Pay click mints another transaction (T3378).
    _postfinance_odoo_pending_states = (
        "CREATE",
        "PENDING",
        "CONFIRMED",
        "PROCESSING",
        "AUTHORIZED",
        "COMPLETED",
    )

    def _postfinance_sync_odoo_state(self):
        for tx in self:
            postfinance_state = tx.postfinance_state
            if postfinance_state in self._postfinance_odoo_pending_states:
                if tx.state == "draft":
                    # Not _set_transaction_pending(): sale's override of it emails
                    # an order confirmation to the donor on every Pay click.
                    tx.write({"state": "pending"})
            elif postfinance_state in ("FAILED", "DECLINE") and tx.state == "pending":
                # _set_transaction_cancel() only accepts draft/authorized, so a
                # failed payment would stay stuck in 'pending'.
                tx.write({"state": "cancel", "date": fields.Datetime.now()})
            elif postfinance_state == "FULFILL" and tx.state == "cancel":
                # Paid after we gave up on it. Only the last attempt may be
                # revived, so two workers racing cannot both book the payment.
                siblings = tx._sibling_transactions()
                if "done" not in siblings.mapped("state") and tx.id > max(
                    siblings.ids, default=0
                ):
                    tx.write(
                        {
                            "state": "done",
                            "date": fields.Datetime.now(),
                            "state_message": "",
                        }
                    )
            if tx.state == "done" and tx.acquirer_reference:
                tx._cancel_superseded_transactions()

    def _postfinance_abandon_pending(self):
        """PostFinance stays PENDING for minutes after a cancel, and a pending
        transaction makes website_sale drop the cart from the session (T3428).

        The date matters: payment_status_poll skips transactions without one, and
        the donor gets "we cannot find your payment" instead of the cancellation.
        """
        self.filtered(lambda tx: tx.state == "pending").write(
            {"state": "cancel", "date": fields.Datetime.now()}
        )

    def _sibling_transactions(self):
        """The paid module reuses one gateway transaction across Pay clicks."""
        self.ensure_one()
        if not self.acquirer_reference:
            return self.browse()
        return self.search(
            [
                ("id", "!=", self.id),
                ("acquirer_reference", "=", self.acquirer_reference),
                ("acquirer_id.provider", "=", "postfinance"),
            ]
        )

    def _cancel_superseded_transactions(self):
        """The paid module only cancels superseded rows still in 'draft', so
        since T3378 they would hang forever.
        """
        self._sibling_transactions().filtered(
            lambda tx: tx.state in ("draft", "pending")
        ).write({"state": "cancel"})

    def _postfinance_form_validate(self, data):
        """Take the row lock in a savepoint before letting the paid module run.

        The paid module takes SELECT ... FOR UPDATE NOWAIT and, on 55P03
        (lock_not_available), logs it and passes. But PostgreSQL aborts the whole
        transaction on that error, so every later query in the same request fails
        and the request rolls back - the sponsor never gets their order confirmed.

        Acquiring the lock here first means a 55P03 only rolls back to the
        savepoint, leaving the cursor usable. If we cannot get the lock, another
        process is already handling this transaction, so we return False (what the
        paid module returns in that case) without calling it at all.
        """
        try:
            with self.env.cr.savepoint(flush=False):
                self.env.cr.execute(
                    "SELECT 1 FROM payment_transaction WHERE id = %s FOR UPDATE NOWAIT",
                    [self.id],
                    log_exceptions=False,
                )
        except OperationalError as error:
            if error.pgcode == "55P03":
                _logger.info(
                    "PostFinance transaction %s is locked by another process, "
                    "skipping this pass.",
                    self.id,
                )
                return False
            raise
        # We now hold the lock, so the paid module's own FOR UPDATE NOWAIT is a
        # no-op within this same transaction.
        res = super()._postfinance_form_validate(data)
        self._postfinance_sync_odoo_state()
        return res
