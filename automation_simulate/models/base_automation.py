# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models

SYNC_FIELDS = {"name", "active", "model_id"}


class BaseAutomation(models.Model):
    _inherit = "base.automation"

    @api.model_create_multi
    def create(self, vals_list):
        automations = super().create(vals_list)
        self.env["automation.simulate.target"]._sync()
        return automations

    def write(self, vals):
        res = super().write(vals)
        if SYNC_FIELDS & set(vals):
            self.env["automation.simulate.target"]._sync()
        return res

    def unlink(self):
        res = super().unlink()
        self.env["automation.simulate.target"]._sync()
        return res
