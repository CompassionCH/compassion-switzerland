##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class MassMailingContact(models.Model):

    _inherit = "mail.mass_mailing.contact"

    partner_id = fields.Many2one(
        "res.partner", "Associated contact", ondelete="cascade",
    )

    @api.model
    def create(self, vals_list):
        records = super().create(vals_list)
        for contact in records:
            if not contact.partner_id:
                contact.write({"partner_id": contact.get_partner(contact.email)})
        return records

    @api.multi
    def get_partner(self, email):
        """Override to fetch partner directly from relation if set."""
        self.ensure_one()
        if self.partner_id:
            return self.partner_id.id
        else:
            return super().get_partner(email)
