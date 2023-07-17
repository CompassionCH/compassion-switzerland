##############################################################################
#
#    Copyright (C) 2016-2022 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class PartnerCommunication(models.Model):
    """Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """

    _inherit = "partner.communication.job"

    product_id = fields.Many2one("product.product", "QR Bill for fund", readonly=False)
    display_pp = fields.Boolean(
        string="Display PP",
        help="If not set, the PP is not printed upper the address.",
        default=True,
    )

    @api.model
    def _get_default_vals(self, vals, default_vals=None):
        if default_vals is None:
            default_vals = []
        default_vals.append("display_pp")
        return super()._get_default_vals(vals, default_vals)
