##############################################################################
#
#    Copyright (C) 2016-2024 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author:
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import fields, models


class ReportSettings(models.TransientModel):
    """Settings configuration for Gift Notifications."""

    _inherit = "res.config.settings"

    compassion_qrr = fields.Char(
        "Compassion QRR",
        default="CH2430808007681434347",
        config_parameter='report.compassion_qrr')
