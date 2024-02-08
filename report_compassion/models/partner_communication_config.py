##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class PartnerCommunicationSwitzerlandConfig(models.Model):
    _inherit = "partner.communication.config"

    display_pp = fields.Boolean(
        string="Display PP",
        help="If not set, the PP is not printed upper the address.",
        default=True,
    )
