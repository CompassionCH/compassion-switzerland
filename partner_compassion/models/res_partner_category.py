from odoo import models


class PartnerCategory(models.Model):
    _inherit = "res.partner.category"

    def write(self, vals):
        # Using sudo because ACLs shouldn't produce data inconsistency
        old_partners = self.mapped("partner_ids").sudo()
        super().write(vals)
        new_partners = self.mapped("partner_ids").sudo()
        if "partner_ids" in vals:
            tag_removed = old_partners - new_partners
            if tag_removed:
                tag_removed.mapped("mass_mailing_contact_ids").write(
                    {"tag_ids": [(3, tag_id) for tag_id in self.ids]}
                )
            tag_added = new_partners - old_partners
            prayer = self.env.ref("partner_compassion.res_partner_category_prayer")
            prayer_engagement = self.env.ref("partner_compassion.engagement_pray")
            if tag_added:
                tag_added.mapped("mass_mailing_contact_ids").write(
                    {"tag_ids": [(4, tag_id) for tag_id in self.ids]}
                )
                if prayer in self:
                    for partner in tag_added:
                        partner.engagement_ids += prayer_engagement
            if tag_removed:
                if prayer in self:
                    for partner in tag_removed:
                        partner.engagement_ids -= prayer_engagement
        return True
