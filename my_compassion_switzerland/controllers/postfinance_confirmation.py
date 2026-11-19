from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing
from odoo.addons.payment_postfinance_flex.controllers.main import PostFinanceController


class PostFinanceConfirmation(PostFinanceController):
    """Override of the paid module payment_postfinance_flex, which must not be
    modified directly (proprietary licence)."""

    # Empty disables the hand-off: only an app version registering the scheme
    # can answer it, and stage and prod use different schemes.
    _app_return_param = "my_compassion_switzerland.app_return_url"

    @http.route()
    def postfinance_form_feedback(self, **post):
        """Confirm the payment when the paying browser holds no session.

        The app pays in a browser Odoo never gave a session to, so
        /payment/status tells the donor it cannot find the payment - which is
        what made donors pay a second time (T3378).
        """
        response = super().postfinance_form_feedback(**post)
        if request.session.get(PaymentPostProcessing.MONITORED_TX_ID_KEY):
            return response
        if not self._confirmation_transaction(post.get("txnId")):
            return response
        return request.render(
            "my_compassion_switzerland.postfinance_confirmation",
            {
                "success": request.httprequest.path != self._failed_url,
                "app_return_url": request.env["ir.config_parameter"]
                .sudo()
                .get_param(self._app_return_param),
            },
        )

    @staticmethod
    def _confirmation_transaction(txn_id):
        """Absent means the module bailed out; leave its response alone."""
        try:
            return (
                request.env["payment.transaction"].sudo().browse(int(txn_id)).exists()
            )
        except (TypeError, ValueError):
            return None
