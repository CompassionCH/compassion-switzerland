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

from odoo import models

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    """Override of the paid module payment_postfinance_flex, which must not be
    modified directly (proprietary licence)."""

    _inherit = "payment.transaction"

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
        return super()._postfinance_form_validate(data)
