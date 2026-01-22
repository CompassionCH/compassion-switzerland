##############################################################################
from odoo import fields, models


class ResUser(models.Model):
    _inherit = "res.users"

    digital_signature = fields.Binary("Handwritten signature")
