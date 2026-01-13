from odoo import fields, http
from odoo.http import request

# Import the parent class to inherit
from odoo.addons.my_compassion.controllers.my2_donations import (
    MyCompassionDonationsController,
)


class MyCompassionDonationsControllerSwiss(MyCompassionDonationsController):
    @http.route(
        "/my2/donation/fetch_payment_methods_iframe",
        type="json",
        auth="user",
        website=True,
    )
    def fetch_payment_methods_iframe(self, **kwargs):
        """
        Override the route to force Odoo to use this class
        (MyCompassionDonationsControllerSwiss) instead of the parent class.
        Calling super() preserves the generic logic but ensures 'self' refers to this
        class instance.
        """
        return super().fetch_payment_methods_iframe(**kwargs)

    @http.route("/my2/debug/charge_token", type="json", auth="user", website=True)
    def debug_charge_token(self, group_id):
        return super().debug_charge_token(group_id)

    def _prepare_iframe_redirect(self, acquirer, return_url):
        """
        PostFinance specific: create the transaction via the API, gather
        available payment methods and the JavaScript URL for the iframe.
        Returns a dict with iframe payload or False on error.
        """
        partner = request.env.user.partner_id
        # 1. Create the Transaction Record (Standard Odoo)
        reference = "ADD-METHOD-{}-{}".format(
            partner.id, fields.Datetime.now().strftime("%Y%m%d%H%M%S")
        )

        # Use standard values
        tx_values = {
            "acquirer_id": acquirer.id,
            "reference": reference,
            "amount": 0.0,
            "currency_id": request.website.currency_id.id,
            "partner_id": partner.id,
            "partner_country_id": partner.country_id.id,
            "type": "validation",
            "return_url": return_url,
            # Odoo handles the relative/absolute conversion often, but passing it here is fine
        }

        tx = request.env["payment.transaction"].sudo().create(tx_values)
        request.session["add_method_tx_id"] = tx.id

        iframe_data = tx.sudo()._postfinance_create_validation_session(return_url)

        return iframe_data
