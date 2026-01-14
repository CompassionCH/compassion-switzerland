##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    @author: Samuel Bachmann <samuel.bachmann02@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import werkzeug

from odoo import http
from odoo.http import request

from odoo.addons.payment_postfinance_flex.controllers.main import PostFinanceController

_logger = logging.getLogger(__name__)
STATUS_EXISTING = 'existing'

class MyCompassionPostFinanceController(PostFinanceController):
    @http.route(
        [PostFinanceController._success_url, PostFinanceController._failed_url],
        type="http",
        auth="public",
        csrf=False,
    )
    def postfinance_form_feedback(self, txnId=None, **post):
        """
        Override to process feedback, force local saving of token_ID and redirect.
        """

        try:
            super().postfinance_form_feedback(txnId, **post)
        except Exception:
            _logger.exception(
                "Error in PostFinanceController.postfinance_form_feedback for txnId %s",
                txnId,
            )

        if not txnId:
            _logger.warning("postfinance_form_feedback called without txnId.")
            return werkzeug.utils.redirect("/payment/process")

        try:
            tx = request.env["payment.transaction"].sudo().browse(int(txnId))
            if not tx.exists():
                raise ValueError()
        except (ValueError, TypeError):
            _logger.warning(
                "Transaction %s not found or invalid in postfinance_form_feedback.",
                txnId,
            )
            return werkzeug.utils.redirect("/payment/process")

        # Create PostFinance token if missing
        if not tx.payment_token_id and tx.acquirer_id.provider == "postfinance":
            try:
                self._create_postfinance_token(tx)
                # Ensure the newly created token is visible in current request
                tx.invalidate_cache()
                tx = request.env["payment.transaction"].sudo().browse(int(txnId))
            except Exception:
                _logger.exception(
                    "Failed to create PostFinance token for transaction %s", tx.id
                )

        # Force Odoo standard post-processing for tokenized payments
        if not tx.is_processed and tx.state in ["done", "authorized"]:
            try:
                tx._post_process_after_done()
            except Exception:
                _logger.exception(
                    "Error during _post_process_after_done for transaction %s", tx.id
                )

        # Create recurring contract group for validation transactions
        group = None
        message = ""
        if tx.type == "validation" and tx.state in ["done", "authorized"]:
            try:
                # Call the updated model method
                result = (
                    request.env["recurring.contract.group"]
                    .sudo()
                    .create_from_transaction(tx)
                )

                # Unpack the dictionary
                group = result.get("group")
                message = result.get("message")
                action_status = result.get("status")

            except Exception:
                _logger.exception(
                    "Error creating recurring contract group for transaction %s", tx.id
                )
                message = "An error occurred while saving the payment method."

            # Determine status and message from the method result
        if tx.return_url:
            if group and group.id:
                # REFACTOR: Check the status code, not the string
                if action_status == STATUS_EXISTING:
                    status = "Already Saved"
                else:
                    status = "Success"
            else:
                status = "Error"
                if not message:
                    message = "Could not create contract group."
            try:
                # Build query parameters
                url_parts = list(urlparse(tx.return_url or "/my/donations"))
                query = parse_qs(url_parts[4])

                query.update(
                    {
                        "payment_method_result": [status],
                        "payment_method_message": [message],
                    }
                )

                url_parts[4] = urlencode(query, doseq=True)
                return_url = urlunparse(url_parts)
                return werkzeug.utils.redirect(return_url)
            except Exception:
                _logger.exception(
                    "Error constructing return URL for transaction %s", tx.id
                )
                return werkzeug.utils.redirect("/payment/process")

        return werkzeug.utils.redirect("/payment/process")

    def _create_postfinance_token(self, tx):
        """
        Custom finalization to create or link PostFinance token.
        """
        token = request.env["payment.token"].sudo().create_or_find_postfinance_token(tx)

        if token:
            tx.payment_token_id = token.id
            _logger.info("Token linked successfully: %s", token.name)
        else:
            _logger.error("Failed to link token for tx %s", tx.reference)
