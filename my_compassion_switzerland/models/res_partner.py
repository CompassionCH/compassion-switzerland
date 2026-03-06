from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_translator = fields.Boolean(compute="_compute_is_translator")

    def _compute_is_translator(self):
        """
        Compute if the partner is a translator.
        """
        for partner in self:
            translator = (
                self.env["translation.user"]
                .sudo()
                .search([("partner_id", "=", partner.id)], limit=1)
            )
            partner.is_translator = bool(translator)
