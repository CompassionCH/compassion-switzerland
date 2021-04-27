##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, api


class ResPartnerCategory(models.Model):
    _inherit = "res.partner.category"

    @api.multi
    def update_partner_tags(self):
        # Update mailing contacts and mailchimp when tags are recomputed.
        to_update = self.env["res.partner"]

        for tag in self:
            old_partners = set(tag.mapped("partner_ids").ids)
            tag.mapped("partner_ids.mailing_contact_ids").write({
                "tag_ids": [(3, tag.id)]
            })
            super(ResPartnerCategory, tag).update_partner_tags()
            new_partners = set(tag.mapped("partner_ids").ids)
            tag.mapped("partner_ids.mailing_contact_ids").write({
                "tag_ids": [(4, tag.id)]
            })
            # xor operator. either no longer have this tag or just got it.
            to_update |= self.env["res.partner"].search([("id", "in", list(old_partners ^ new_partners))])

        to_update.process_mailchimp_update()
        return True
