from odoo import api, fields, models


class Lead(models.Model):
    _inherit = "crm.lead"

    # Remove the compute attribute from the email_from field
    email_from = fields.Char(compute=False, inverse=False)

    # Keep possibility to sync email_from with partner email from the UI.
    @api.onchange("partner_id")
    def onchange_partner_id(self):
        if self.partner_id.email:
            self.email_from = self.partner_id.email
