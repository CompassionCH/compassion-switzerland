import re

from odoo import api, fields, models


class ServerActionMonitor(models.Model):
    _name = "server.action.monitor"
    _description = "Server Action Monitor"
    _order = "create_date desc"

    server_action_id = fields.Many2one(
        "ir.actions.server",
        string="Server Action",
        required=True,
        ondelete="cascade",
    )
    execution_time = fields.Char(
        string="Execution Duration",
        readonly=True,
        help="Last execution duration of the job in seconds.",
        required=True,
    )
    execution_time_seconds = fields.Float(
        string="Execution Time (s)",
        compute="_compute_execution_time_seconds",
        store=True,
        readonly=True,
        help="Execution duration in seconds (for sorting/searching).",
    )
    user_id = fields.Many2one("res.users", string="User")
    exception = fields.Text()

    @api.depends("execution_time")
    def _compute_execution_time_seconds(self):
        for rec in self:
            rec.execution_time_seconds = self._parse_time_to_seconds(rec.execution_time)

    @staticmethod
    def _parse_time_to_seconds(time_str):
        if not time_str:
            return 0.0
        # Match hh:mm:ss(.ms) or mm:ss(.ms) or ss(.ms)
        match = re.match(r"^(?:(\d+):)?(?:(\d+):)?(\d+(?:\.\d+)?)$", time_str)
        if not match:
            try:
                return float(time_str)
            except Exception:
                return 0.0
        parts = match.groups(default="0")
        h, m, s = [float(p) for p in parts]
        return h * 3600 + m * 60 + s
