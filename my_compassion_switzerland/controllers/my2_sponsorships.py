##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http

from odoo.addons.my_compassion.controllers.my2_sponsorships import (
    MyCompassionNewSponsorshipController,
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
        token is (see MyCompassionNewSponsorshipController._owns_signup):
        proof of having gone through this exact checkout in this browser, or
        being the authenticated sponsor. A bare sponsorship_id in the
        request proves nothing on its own.

        volunteering must be an actual JSON boolean, not merely truthy: a
        naive bool(volunteering) would coerce the *string* "false" - which
        this is a public JSON route, so any caller may send - to True,
        silently opting a sponsor in while looking like it recorded them
        opting out.

        Unlike the old details-form field this replaces, this also accepts
        unticking: the checkbox now reflects live state on a page the
        sponsor can act from, not a one-shot form, so taking back an
        accidental tick should work the same as giving one.
        """
        if not isinstance(volunteering, bool):
            return {"success": False}
        sponsorship = self._fetch_signup(sponsorship_id)
        if not self._owns_signup(sponsorship):
            return {"success": False}
        sponsorship.partner_id.sudo().write(
            {"interested_for_volunteering": volunteering}
        )
        return {"success": True}
