##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, _
from odoo.exceptions import UserError


class PartnerMergeWizard(models.TransientModel):
    _inherit = "base.partner.merge.automatic.wizard"

    def action_merge(self):
        """
        - Allow anybody to perform the merge of partners
        - Prevent geoengine bugs
        - Prevent to merge sponsors
        - Save other e-mail addresses in linked partners
        """
        removing = self.partner_ids - self.dst_partner_id
        geo_point = self.dst_partner_id.geo_point
        self.partner_ids.write({"geo_point": False})
        sponsorships = self.env["recurring.contract"].search(
            [
                ("correspondent_id", "in", removing.ids),
                ("state", "=", "active"),
                ("type", "like", "S"),
            ]
        )
        if sponsorships:
            raise UserError(
                _(
                    "The selected partners are sponsors! "
                    "Please first modify the sponsorship and don't forget "
                    "to send new labels to them."
                )
            )
        # check onboarding_new_donor_start_date for non-dst partner. If set,
        # and dst partner is sponsor, clear the onboarding_new_donor_start_date.
        if removing.onboarding_new_donor_start_date:
            sponsor_category = self.env.ref(
                "partner_compassion.res_partner_category_sponsor"
            )
            if sponsor_category in self.dst_partner_id.category_id:
                removing.onboarding_new_donor_start_date = False

        if self.dst_partner_id.thankyou_preference == "none":
            self.env["partner.communication.job"].search(
                [("partner_id", "in", removing.ids), ("state", "=", "pending")]
            ).unlink()

        old_emails = removing.filtered("email").mapped("email")
        new_email = self.dst_partner_id.email
        for email in old_emails:
            if new_email and email != new_email:
                self.dst_partner_id.copy(
                    {
                        "contact_id": self.dst_partner_id.id,
                        "email": email,
                        "type": "email_alias",
                    }
                )
        res = super(PartnerMergeWizard, self.sudo()).action_merge()
        self.dst_partner_id.geo_point = geo_point
        return res
