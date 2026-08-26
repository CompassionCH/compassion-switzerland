##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http
from odoo.http import request

from odoo.addons.my_compassion.controllers.my2_sponsorships import (
    OWN_SIGNUPS_SESSION_KEY,
    MyCompassionNewSponsorshipController,
    MyCompassionSponsorshipPayment,
)


class MyCompassionNewSponsorshipControllerSwitzerland(
    MyCompassionNewSponsorshipController
):
    @http.route(
        "/my2/new-sponsorship/volunteering",
        type="json",
        auth="public",
        website=True,
    )
    def sponsorship_volunteering_optin(
        self, sponsorship_id=None, volunteering=None, **kwargs
    ):
        """Sets the Swiss volunteering opt-in from the "All set" page.

        That page (my_compassion.my2_new_sponsorship_thank_you_page, the
        request.env.user._is_public() branch) has no form of its own to post
        through - it is a summary, not a step - so the checkbox posts here
        by itself instead, on change. Gated the same way the details-form
        token is (see MyCompassionNewSponsorshipController
        ._issue_details_token): proof of having gone through this exact
        checkout in this browser, or being the authenticated sponsor. A bare
        sponsorship_id in the request proves nothing on its own.

        Unlike the old details-form field this replaces, this also accepts
        unticking: the checkbox now reflects live state on a page the
        sponsor can act from, not a one-shot form, so taking back an
        accidental tick should work the same as giving one.
        """
        sponsorship = self._fetch_signup(sponsorship_id)
        owns_signup = sponsorship.id in (
            request.session.get(OWN_SIGNUPS_SESSION_KEY) or []
        )
        if not owns_signup and not MyCompassionSponsorshipPayment._is_sponsorship_user(
            sponsorship
        ):
            return {"success": False}
        sponsorship.partner_id.sudo().write(
            {"interested_for_volunteering": bool(volunteering)}
        )
        return {"success": True}
