from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        if "email" in vals:
            # Propagate the email change to the related crm.lead
            for partner in self:
                opportunities = self.env["crm.lead"].search(
                    [
                        ("partner_id", "=", partner.id),
                        ("email_from", "=", partner.email),
                    ]
                )
                opportunities.write({"email_from": vals["email"]})
        super().write(vals)
        return True
