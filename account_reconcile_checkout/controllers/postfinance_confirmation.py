##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from urllib.parse import urlparse

import werkzeug

from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.addons.payment_postfinance_flex.controllers.main import PostFinanceController

CHECKOUT_URL_SESSION_KEY = "__postfinance_checkout_url"


def release_postfinance_attempt(confirm_id=None):
    """Cancel the PostFinance payment this session started, if still pending.

    Both callers are public routes, so the record always comes from the session;
    confirm_id may only confirm it, never select it. Returns what was released.
    """
    attempt = request.session.get("__website_sale_last_tx_id")
    if not attempt:
        return request.env["payment.transaction"]
    if confirm_id is not None and str(confirm_id or "") != str(attempt):
        return request.env["payment.transaction"]
    released = (
        request.env["payment.transaction"]
        .sudo()
        .browse(attempt)
        .exists()
        .filtered(
            lambda tx: tx.acquirer_id.provider == "postfinance"
            and tx.state == "pending"
        )
    )
    released._postfinance_abandon_pending()
    return released


def store_checkout_url():
    """Remember the page the donor is paying from, to return them there.

    A path on our own host only: the value comes from a request header, so
    anything else would let a crafted referrer steer the cancel redirect.
    """
    referrer = urlparse(request.httprequest.referrer or "")
    path = referrer.path
    if referrer.netloc and referrer.netloc != request.httprequest.host:
        path = ""
    if not path.startswith("/") or path.startswith("//"):
        path = ""
    request.session[CHECKOUT_URL_SESSION_KEY] = path


def checkout_url():
    return request.session.get(CHECKOUT_URL_SESSION_KEY) or "/shop/payment"


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
        if request.httprequest.path == self._failed_url:
            if release_postfinance_attempt(txnId):
                # Back to the payment methods rather than the dead-end status
                # page: the donor cancelled to pick a different one (T3428).
                return werkzeug.utils.redirect(checkout_url())
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
