from odoo import http
from odoo.http import request

# Import the parent class to inherit
from odoo.addons.my_compassion.controllers.my2_donations import (
    MyCompassionDonationsController,
)


class MyCompassionDonationsControllerSwiss(MyCompassionDonationsController):
    @http.route(
        "/my2/donation/add_payment_method_online",
        type="json",
        auth="user",
        website=True,
    )
    def add_payment_method_online(self, **kwargs):
        """
        Override the route to force Odoo to use this class
        (MyCompassionDonationsControllerSwiss) instead of the parent class.
        Calling super() preserves the generic logic but ensures 'self' refers to this
        class instance.
        """
        return super(
            MyCompassionDonationsControllerSwiss, self
        ).add_payment_method_online(**kwargs)

    @http.route("/my2/debug/charge_token", type="json", auth="user", website=True)
    def debug_charge_token(self, group_id):
        return super().debug_charge_token(group_id)

    def _prepare_postfinance_iframe_redirect(self, acquirer, tx, return_url):
        """
        PostFinance specific: create the transaction via the API, gather
        available payment methods and the JavaScript URL for the iframe.
        Returns a dict with iframe payload or False on error.
        """
        if acquirer.provider != "postfinance":
            return False  # Other providers are not handled for now

        # 1. Convert relative URL to absolute (Required by PostFinance)
        base_url = request.httprequest.host_url
        if return_url and return_url.startswith("/"):
            return_url = base_url.rstrip("/") + return_url

        # 1. Prepare Transaction Data
        tx_values = {
            "tx_details": {
                "currency_name": tx.currency_id.name,
                "name": tx.reference,
                "partner_id": tx.partner_id.id,
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
            # False allows us to fetch all available methods later
            "postfinance_payment_method": False,
            "billing_address": {
                "city": tx.partner_id.city or "",
                "emailAddress": tx.partner_id.email or "",
                "givenName": tx.partner_id.firstname or tx.partner_id.name or "",
                "familyName": tx.partner_id.lastname or "",
                "postCode": tx.partner_id.zip or "",
                "street": tx.partner_id.street or "",
                "country": tx.partner_id.country_id.code or "CH",
            },
        }

        try:
            # 2. Create Transaction
            create_res = acquirer.sudo().postfinance_create_transation(
                acquirer.id, tx_values
            )
            pf_trans_id = create_res.get("trans_id")

            if not pf_trans_id:
                return False

            tx.sudo().write({"acquirer_reference": pf_trans_id})

            # 3. Fetch All Possible Payment Methods (Generalization)
            space_id = acquirer.postfinance_api_spaceid
            method_uri = (
                f"/api/v2.0/payment/transactions/{pf_trans_id}"
                "/payment-method-configurations?integrationMode=iframe"
            )
            headers = {"space": str(space_id)}

            method_res = acquirer.sudo()._postfinance_send_request(
                acquirer.id, "GET", method_uri, headers=headers
            )
            available_methods = []

            if method_res.get("status") == 200:
                response_body = method_res.get("data", {})
                payment_configs = response_body.get("data", [])

                current_lang = request.lang or "en-US"

                for m in payment_configs:  # Iterate over the list, not the dict
                    # Resolve name based on language or fallback
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
                    )  # 4. Get JavaScript URL for Iframe
            url_res = acquirer.sudo().postfinance_build_javascript_url(
                acquirer.id, pf_trans_id
            )

            return {
                "type": "iframe",
                "url": url_res.get("postfinance_javascript_url"),
                "pf_methods": available_methods,  # List of all active methods
            }

        except Exception:
            return False
