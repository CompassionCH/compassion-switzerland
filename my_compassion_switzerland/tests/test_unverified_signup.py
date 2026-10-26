##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.tests import tagged
from odoo.tests.common import HttpCase

from odoo.addons.my_compassion.controllers.my2_sponsorships import (
    OWN_SIGNUPS_SESSION_KEY,
)
from odoo.addons.my_compassion.tests.test_unverified_signup import (
    UnverifiedSignupCase,
)


@tagged("post_install", "-at_install")
class TestUnverifiedSignupVolunteering(HttpCase, UnverifiedSignupCase):
    """The volunteering opt-in of the "All set" page writes the partner of
    the signup: the visitor's own, never the known donor whose email they
    typed."""

    def test_the_opt_in_never_reaches_the_known_donor(self):
        self.donor.interested_for_volunteering = False
        sponsorship = self._sign_up(firstname="Known", lastname="Donor")
        self.authenticate(
            None, None, session_extra={OWN_SIGNUPS_SESSION_KEY: [sponsorship.id]}
        )
        result = self.make_jsonrpc_request(
            "/my2/new-sponsorship/volunteering",
            {"sponsorship_id": sponsorship.id, "volunteering": True},
        )
        self.assertTrue(result["success"])
        self.assertTrue(sponsorship.partner_id.interested_for_volunteering)
        self.assertFalse(self.donor.interested_for_volunteering)
        # and the donor's own signup stays out of this browser's reach
        result = self.make_jsonrpc_request(
            "/my2/new-sponsorship/volunteering",
            {"sponsorship_id": self.donor_contract.id, "volunteering": True},
        )
        self.assertFalse(result["success"])
        self.assertFalse(self.donor.interested_for_volunteering)
