##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    @author: Samuel Bachmann <samuel.bachmann02@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class PaymentAcquirerPostFinance(models.Model):
    _inherit = "payment.acquirer"

    def postfinance_charge_token(self, token, amount, currency, reference, partner_id):
        """
        Server-to-Server (S2S) charge of an existing PostFinance Token.
        :param token: payment.token record
        :param amount: float
        :param currency: res.currency record
        :param reference: str (unique merchant reference, e.g. INV/2025/001)
        :param partner_id: res.partner record
        """
        self.ensure_one()

        if self.provider != "postfinance":
            return {"success": False, "error": "Invalid provider"}

        if not token.acquirer_ref:
            return {"success": False, "error": "Token has no PostFinance ID"}

        try:
            pf_token_id = int(token.acquirer_ref)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid Token ID: {token.acquirer_ref}",
            }

        # 1. Prepare Payload
        tx_values = {
            "currency": currency.name,
            "lineItems": [
                {
                    "amountIncludingTax": amount,
                    "name": _("Subscription Charge"),
                    "quantity": 1,
                    "type": "PRODUCT",
                    "uniqueId": "recurring_charge",
                    "sku": "monthly_sub",
                }
            ],
            "token": pf_token_id,
            "autoConfirmationEnabled": True,
            "chargeRetryEnabled": False,
            "merchantReference": reference,
            "billingAddress": {
                "country": partner_id.country_id.code or "CH",
                "emailAddress": partner_id.email or "",
                "familyName": partner_id.lastname or partner_id.name or "",
                "givenName": partner_id.firstname or "",
            },
        }

        try:
            space_id = self.postfinance_api_spaceid

            # Header requirements: The 'space' ID is required in the header
            uri = "/api/v2.0/payment/transactions"
            headers = {"space": str(space_id)}

            # Send Request
            resp = self._postfinance_send_request(
                self.id, "POST", uri, json_data=tx_values, headers=headers
            )

            if resp.get("status") not in [200, 201]:
                return {"success": False, "error": resp.get("error", "API Error")}

            data = resp.get("data", {})
            state = data.get("state")
            transaction_id = data.get("id")

            # 2. Force Processing
            if state == "PENDING":
                _logger.info(
                    f"Tx {transaction_id} PENDING. Processing without interaction..."
                )

                process_uri = (
                    f"/api/v2.0/payment/transactions/{transaction_id}"
                    f"/process-without-interaction"
                )

                # Ensure space header is passed again
                process_resp = self._postfinance_send_request(
                    self.id, "POST", process_uri, headers=headers
                )

                if process_resp.get("status") == 200:
                    data = process_resp.get("data", {})
                    state = data.get("state")

            # 3. Final State Check
            if state in ["AUTHORIZED", "COMPLETED", "FULFILL", "PROCESSING"]:
                return {
                    "success": True,
                    "transaction_id": transaction_id,
                    "state": state,
                }
            else:
                fail_reason = data.get("failureReason", {}).get(
                    "description", "No reason"
                )
                return {
                    "success": False,
                    "error": f"State: {state} | Reason: {fail_reason}",
                    "transaction_id": transaction_id,
                }

        except Exception as e:
            _logger.exception("Exception during PostFinance Token Charge")
            return {"success": False, "error": str(e)}
