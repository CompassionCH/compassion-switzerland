# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models

from .automation_simulate_target import ENABLED_PARAM


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    automation_simulate_enabled = fields.Boolean(
        "Simulate automations", config_parameter=ENABLED_PARAM
    )
