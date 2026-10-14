# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models

SYNC_FIELDS = {"name", "active", "model_id", "ir_actions_server_id"}


class IrCron(models.Model):
    _inherit = "ir.cron"

    @api.model_create_multi
    def create(self, vals_list):
        crons = super().create(vals_list)
        self.env["automation.simulate.target"]._sync()
        return crons

    def write(self, vals):
        res = super().write(vals)
        if SYNC_FIELDS & set(vals):
            self.env["automation.simulate.target"]._sync()
        return res

    def unlink(self):
        res = super().unlink()
        self.env["automation.simulate.target"]._sync()
        return res
