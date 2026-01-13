##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    @author: Samuel Bachmann <samuel.bachmann02@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _postfinance_create_validation_session(self, return_url):
        """
        Orchestrates the creation of the PostFinance transaction
        and fetching of methods for the iframe.
        """
        self.ensure_one()

        # 1. Prepare absolute URL (Util/Controller logic moved here or kept clean)
        base_url = self.acquirer_id.get_base_url()
        if return_url and return_url.startswith("/"):
            return_url = base_url.rstrip("/") + return_url

        # 2. Build the Payload
        # Use existing fields on self (self.partner_id, self.amount, etc)
        tx_values = {
            "tx_details": {
                "currency_name": self.currency_id.name,
                "name": self.reference,
                "partner_id": self.partner_id.id,
            },
            "txline_details": [
                {
                    "name": "Validation",
                    "quantity": 1,
                    "type": "PRODUCT",
                    "uniqueId": "validation",
                    "amountIncludingTax": 0.0,
                }
            ],
            "postfinance_payment_method": False,
            "billing_address": self._postfinance_get_billing_address(),  # Refactored into helper
        }

        try:
            # 3. Call Acquirer API
            create_res = self.acquirer_id.postfinance_create_transation(
                self.acquirer_id.id, tx_values
            )
            pf_trans_id = create_res.get("trans_id")

            if not pf_trans_id:
                return False

            # 4. Update Self
            self.write({"acquirer_reference": pf_trans_id})

            # 5. Fetch Payment Methods (Logic moved from Controller)
            available_methods = self._postfinance_fetch_iframe_methods(pf_trans_id)

            # 6. Get JS URL
            url_res = self.acquirer_id.postfinance_build_javascript_url(
                self.acquirer_id.id, pf_trans_id
            )

            return {
                "type": "iframe",
                "url": url_res.get("postfinance_javascript_url"),
                "pf_methods": available_methods,
            }

        except Exception:
            # Log the specific error here using _logger
            return False

    def _postfinance_get_billing_address(self):
        """Helper to format address for PostFinance"""
        partner = self.partner_id
        return {
            "city": partner.city or "",
            "emailAddress": partner.email or "",
            "givenName": partner.firstname or partner.name or "",
            "familyName": partner.lastname or "",
            "postCode": partner.zip or "",
            "street": partner.street or "",
            "country": partner.country_id.code or "CH",
        }

    def _postfinance_fetch_iframe_methods(self, pf_trans_id):
        """Helper to fetch and parse payment methods"""
        space_id = self.acquirer_id.postfinance_api_spaceid
        method_uri = (
            f"/api/v2.0/payment/transactions/{pf_trans_id}"
            "/payment-method-configurations?integrationMode=iframe"
        )
        headers = {"space": str(space_id)}

        method_res = self.acquirer_id._postfinance_send_request(
            self.acquirer_id.id, "GET", method_uri, headers=headers
        )

        available_methods = []
        if method_res.get("status") == 200:
            response_body = method_res.get("data", {})
            payment_configs = response_body.get("data", [])

            # Use Odoo Context for lang if available, or fallback
            current_lang = self.env.context.get("lang", "en-US")

            for m in payment_configs:
                title_map = m.get("resolvedTitle", {})
                name = (
                    title_map.get(current_lang)
                    or title_map.get("en-US")
                    or m.get("name")
                )
                available_methods.append(
                    {
                        "id": m.get("id"),
                        "name": name,
                        "image": m.get("resolvedImageUrl"),
                    }
                )
        return available_methods
