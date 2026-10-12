# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from datetime import timedelta

from odoo import SUPERUSER_ID, api, fields, models
from odoo.tools import SQL

_logger = logging.getLogger(__name__)

RETENTION_PARAM = "base_cron_monitor.retention_days"
DEFAULT_RETENTION_DAYS = 30


class ServerActionMonitor(models.Model):
    _name = "server.action.monitor"
    _description = "Server Action Monitor"
    _order = "create_date desc, id desc"

    server_action_id = fields.Many2one(
        "ir.actions.server",
        string="Server Action",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
    )
    usage = fields.Selection(related="server_action_id.usage", store=True)
    user_id = fields.Many2one("res.users", string="User", readonly=True)
    run_count = fields.Integer(
        "Executions",
        readonly=True,
        aggregator="sum",
        help="Successful executions of the action by the user in the same "
        "transaction are grouped in one log.",
    )
    duration = fields.Float(
        "Total Duration (s)",
        readonly=True,
        aggregator="sum",
        digits=(16, 3),
    )
    max_duration = fields.Float(
        "Longest Execution (s)",
        readonly=True,
        aggregator="max",
        digits=(16, 3),
    )
    exception = fields.Text(readonly=True)

    @api.model
    def _insert_logs(self, rows):
        """Insert the logs in one query, without going through the ORM: it
        doesn't trigger automation rules (that would be monitored again) nor
        any other side effect.

        :param rows: list of tuples
            (server_action_id, user_id, run_count, duration, max_duration, exception)
        """
        cr = self.env.cr
        # Never wait long for a lock: we hold none, but we'd rather lose logs
        # than slow down the request that produced them.
        cr.execute("SET LOCAL lock_timeout = '2s'")
        values = SQL(", ").join(SQL("(%s, %s, %s, %s, %s, %s)", *row) for row in rows)
        cr.execute(
            SQL(
                """
                INSERT INTO server_action_monitor (
                    server_action_id, user_id, run_count, duration, max_duration,
                    exception, usage, create_uid, write_uid, create_date, write_date
                )
                SELECT v.action_id, u.id, v.run_count, v.duration, v.max_duration,
                       v.exception, a.usage, %(uid)s, %(uid)s,
                       now() AT TIME ZONE 'UTC', now() AT TIME ZONE 'UTC'
                FROM (VALUES %(values)s) AS v(
                    action_id, user_id, run_count, duration, max_duration, exception
                )
                -- skip actions deleted in the meantime
                JOIN ir_act_server a ON a.id = v.action_id
                LEFT JOIN res_users u ON u.id = v.user_id
                """,
                uid=SUPERUSER_ID,
                values=values,
            )
        )

    @api.autovacuum
    def _gc_monitor_logs(self):
        days = int(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(RETENTION_PARAM, DEFAULT_RETENTION_DAYS)
        )
        limit = fields.Datetime.now() - timedelta(days=days)
        self.env.cr.execute(
            SQL("DELETE FROM server_action_monitor WHERE create_date < %s", limit)
        )
        _logger.info("Removed %s server action monitor logs", self.env.cr.rowcount)
