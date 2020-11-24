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
        for tag in self:
            tag.mapped("partner_ids.mailing_contact_ids").write({
                "tag_ids": [(3, tag.id)]
            })
        super().update_partner_tags()
        for tag in self:
            tag.mapped("partner_ids.mailing_contact_ids").write({
                "tag_ids": [(4, tag.id)]
            })
        self.env["mail.mass_mailing.contact"] \
            .with_delay().update_all_merge_fields_job(self.mapped("partner_ids").ids)
        return True
