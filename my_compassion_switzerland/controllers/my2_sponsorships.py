##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.my_compassion.controllers.my2_sponsorships import (
    MyCompassionNewSponsorshipController,
)


class MyCompassionNewSponsorshipControllerSwitzerland(
    MyCompassionNewSponsorshipController
):
    # A classmethod where the shared implementation is a staticmethod, so
    # that super() can reach it: the two are called the same way (through the
    # instance), and this is the only shape that composes if a third module
    # ever adds a field of its own here too.
    @classmethod
    def _details_form_values(cls, post):
        """Read the Swiss volunteering opt-in out of the details form too.

        The one field templates/my2_new_sponsorship_wizard.xml adds to that
        form. Carried through the shared plumbing untouched: it ends up in
        the values recurring.contract._my2_apply_details saves, and - when a
        required field comes back empty - in the prefill that re-renders the
        form, so the tick survives the bounce.
        """
        values = super()._details_form_values(post)
        values["volunteering"] = bool(post.get("volunteering"))
        return values
