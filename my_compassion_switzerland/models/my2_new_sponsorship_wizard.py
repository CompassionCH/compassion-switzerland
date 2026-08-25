##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models


class NewSponsorshipWizard(models.TransientModel):
    _inherit = "new.sponsorship.wizard"

    # The volunteering opt-in, when a step of the flow asks it before the
    # payment. No step does since the fast checkout: the live path is the
    # post-payment details form (see templates/my2_new_sponsorship_wizard.xml
    # and recurring_contract._my2_apply_details). Kept because this is the
    # seam a pre-payment step would use again, and because it is what puts an
    # explicit value on the partner at creation time instead of leaving the
    # column NULL.
    volunteering = fields.Boolean()

    def update(self, post):
        res = super().update(post)
        if "volunteering" in post:
            self.volunteering = bool(post["volunteering"])
        return res

    def _get_new_partner_vals(self):
        """Add the volunteering flag to the partner of a public signup.

        Purely additive on top of the shared implementation, including its
        placeholder-name handling: that one rewrites the name keys of a
        signup whose sponsor has not given a name yet, and this key is not
        one of them.
        """
        vals = super()._get_new_partner_vals()
        vals["interested_for_volunteering"] = self.volunteering
        return vals
