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

    volunteering = fields.Boolean()

    def update(self, post):
        res = super().update(post)
        if "volunteering" in post:
            self.volunteering = bool(post["volunteering"])
        return res

    def _get_new_partner_vals(self):
        vals = super()._get_new_partner_vals()
        vals["interested_for_volunteering"] = self.volunteering
        return vals
