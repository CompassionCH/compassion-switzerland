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
            old_partners = set(tag.mapped("partner_ids").ids)
            tag.mapped("partner_ids.mailing_contact_ids").write({
                "tag_ids": [(3, tag.id)]
            })
            super(ResPartnerCategory, tag).update_partner_tags()
            new_partners = set(tag.mapped("partner_ids").ids)
            tag.mapped("partner_ids.mailing_contact_ids").write({
                "tag_ids": [(4, tag.id)]
            })
            for partner_id in old_partners ^ new_partners:
                queue_job = self.env["queue.job"].search([
                    ("channel", "=", "root.mass_mailing_switzerland.update_partner_mailchimp"),
                    ("state", "!=", "done"),
                ])
                if len(queue_job) and partner_id in queue_job.mapped("args"):
                    continue
                self.env["mail.mass_mailing.contact"] \
                    .with_delay().update_partner_merge_fields_job(partner_id)
        return True
