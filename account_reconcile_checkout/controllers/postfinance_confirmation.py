##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from urllib.parse import urlparse

from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.payment_postfinance_flex.controllers.main import PostFinanceController


class PostFinanceConfirmation(PostFinanceController):
    """Override of the paid module payment_postfinance_flex, which must not be
    modified directly (proprietary licence)."""

    _app_return_url = "mycompassion://payment/done"
    _app_return_param = "account_reconcile_checkout.app_return_enabled"

    @http.route()
    def postfinance_form_feedback(self, txnId=None, **post):
        """Confirm the payment when the paying browser holds no session.

        The app pays in a browser Odoo never gave a session to, so
        /payment/process tells the donor it cannot find the payment - which is
        what made testers pay a second time (T3378).
        """
        response = super().postfinance_form_feedback(txnId=txnId, **post)
        next_url = getattr(response, "headers", {}).get("Location") or ""
        # Only the normal hand-off, never the module's own error page.
        if urlparse(next_url).path.rstrip("/") != "/payment/process":
            return response
        if PaymentProcessing.get_payment_transaction_ids():
            return response
        return request.render(
            "account_reconcile_checkout.postfinance_confirmation",
            {
                "success": request.httprequest.path != self._failed_url,
                "app_return_url": self._app_return_url_if_enabled(),
            },
        )

    def _app_return_url_if_enabled(self):
        """Off until an app version registering the scheme is live: older ones
        answer it with a browser error page.
        """
        enabled = (
            request.env["ir.config_parameter"].sudo().get_param(self._app_return_param)
        )
        return self._app_return_url if enabled in ("1", "True", "true") else False
