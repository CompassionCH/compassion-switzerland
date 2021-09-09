##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class ResPartnerCategory(models.Model):
    _inherit = "res.partner.category"

    name = fields.Char(translate=False)

    @api.multi
    def update_partner_tags(self):
        all_partners_to_update = self.env["res.partner"]
        # Update mailing contacts and mailchimp when tags are recomputed.
        for tag in self.with_context(skip_mailchimp_sync=True):
            old_partners = set(tag.mapped("partner_ids").ids)
            tag.mapped("partner_ids.mass_mailing_contact_ids").write({
                "tag_ids": [(3, tag.id)]
            })
            super(ResPartnerCategory, tag).update_partner_tags()
            new_partners = set(tag.mapped("partner_ids").ids)
            tag.mapped("partner_ids.mass_mailing_contact_ids").write({
                "tag_ids": [(4, tag.id)]
            })
            to_update_for_tag = old_partners ^ new_partners
            all_partners_to_update |= self.env["res.partner"].browse(to_update_for_tag)

        all_partners_to_update.mapped("mass_mailing_contact_ids").process_mailchimp_update()
        return True
