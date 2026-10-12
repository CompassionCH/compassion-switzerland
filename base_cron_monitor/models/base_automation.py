# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class BaseAutomation(models.Model):
    _inherit = "base.automation"

    def action_open_monitor_logs(self):
        return self.action_server_ids.action_open_monitor_logs()
