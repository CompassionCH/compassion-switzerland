##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http

from odoo.addons.website_sale.controllers.main import WebsiteSale

from .postfinance_confirmation import release_postfinance_attempt


class WebsiteSalePostFinance(WebsiteSale):
    @http.route()
    def payment(self, **post):
        """Reaching this page means no payment form is open.

        The card form is a dialog rendered on this very page and its close button
        only calls location.reload (postfinance_interface.js), so the donor comes
        back with the attempt still pending - which hides the cart and bounces
        them to /shop (T3428).
        """
        release_postfinance_attempt()
        return super().payment(**post)
