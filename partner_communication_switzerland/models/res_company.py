from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    # Translate name of Company for signatures
    address_name = fields.Char(translate=True)
