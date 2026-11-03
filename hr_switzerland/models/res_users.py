##############################################################################
from odoo import fields, models


class ResUser(models.Model):
    _inherit = "res.users"

    digital_signature = fields.Binary("Handwritten signature")

    @property
    def SELF_READABLE_FIELDS(self):
        # Shown in "My Profile": without it, the user's own HR fields are
        # refused there (T3604).
        return super().SELF_READABLE_FIELDS + ["digital_signature"]
