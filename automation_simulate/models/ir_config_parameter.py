# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models

from .automation_simulate_target import ENABLED_PARAM


class IrConfigParameter(models.Model):
    _inherit = "ir.config_parameter"

    @api.model_create_multi
    def create(self, vals_list):
        params = super().create(vals_list)
        if ENABLED_PARAM in params.mapped("key"):
            self.env["automation.simulate.target"]._sync()
        return params

    def write(self, vals):
        keys = set(self.mapped("key"))
        res = super().write(vals)
        if ENABLED_PARAM in keys | set(self.mapped("key")):
            self.env["automation.simulate.target"]._sync()
        return res

    def unlink(self):
        sync = ENABLED_PARAM in self.mapped("key")
        res = super().unlink()
        if sync:
            self.env["automation.simulate.target"]._sync()
        return res
