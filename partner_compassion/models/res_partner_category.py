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
                contacts = tag_removed.mapped("mass_mailing_contact_ids")
                if contacts:
                    contacts.with_delay_sh(
                        "write",
                        {"tag_ids": [(3, tag_id) for tag_id in self.ids]},
                        priority=100,
                        channel="root.mailchimp",
                        split=80,
                    )
            tag_added = new_partners - old_partners
            prayer = self.env.ref("partner_compassion.res_partner_category_prayer")
            prayer_engagement = self.env.ref("partner_compassion.engagement_pray")
            if tag_added:
                contacts = tag_added.mapped("mass_mailing_contact_ids")
                if contacts:
                    contacts.with_delay_sh(
                        "write",
                        {"tag_ids": [(4, tag_id) for tag_id in self.ids]},
                        priority=100,
                        channel="root.mailchimp",
                        split=80,
                    )
                if prayer in self:
                    for partner in tag_added:
                        partner.engagement_ids += prayer_engagement
            if tag_removed:
                if prayer in self:
                    for partner in tag_removed:
                        partner.engagement_ids -= prayer_engagement
        return True

    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        new_name = self.name + " (copy)"
        default.update({"name": new_name})
        new_filter = False
        if self.tag_filter_condition_id:
            new_filter = self.tag_filter_condition_id.copy({"name": new_name})
            default["tag_filter_condition_id"] = new_filter.id
        new = super(PartnerCategory, self.with_context(lang=None)).copy(default)
        for lang in self.env["res.lang"].search([]):
            new.with_context(lang=lang.code).name = new_name
            if new_filter:
                new_filter.with_context(lang=lang.code).name = new_name
        return new
