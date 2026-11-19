from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    font = fields.Selection(
        selection_add=[("NeighbourSans", "NeighbourSans")],
        ondelete={"NeighbourSans": "set default"},
    )
    official_signer_id = fields.Many2one(
        "hr.employee",
        string="Official Signer",
        help="Employee whose name and signature appear on official "
        "documents (e.g. tax receipts) that are not tied to a specific "
        "staff member. Left empty, those documents fall back to a plain "
        "company sign-off with no personal name or image.",
    )

    def _get_signature_closing_line(self):
        """Generic 'company only' sign-off line, e.g. 'Compassion Suisse' -
        used both as the no-employee fallback in res.users.signature_letter
        and directly by documents with no signer configured at all."""
        self.ensure_one()
        return self.name.split(" ")[0] + " " + self.country_id.name

    # Translate company fields for our audience info
    commercial_name = fields.Char(translate=True)
    commercial_street = fields.Char(translate=True)
    commercial_city = fields.Char(translate=True)
    commercial_zip = fields.Char(translate=True)
    commercial_phone = fields.Char(translate=True)
    social_facebook = fields.Char(translate=True)
    social_youtube = fields.Char(translate=True)
    social_vimeo = fields.Char()
