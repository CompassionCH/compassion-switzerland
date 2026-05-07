from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    font = fields.Selection(
        selection_add=[("NeighbourSans", "NeighbourSans")],
        ondelete={"NeighbourSans": "set default"},
    )
    # Translate company fields for our audience info
    commercial_name = fields.Char(translate=True)
    commercial_street = fields.Char(translate=True)
    commercial_city = fields.Char(translate=True)
    commercial_zip = fields.Char(translate=True)
    commercial_phone = fields.Char(translate=True)
    social_facebook = fields.Char(translate=True)
    social_youtube = fields.Char(translate=True)
    social_vimeo = fields.Char()
