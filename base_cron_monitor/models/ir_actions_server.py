# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import time
import traceback

from odoo import models

_logger = logging.getLogger(__name__)

BUFFER_KEY = "base_cron_monitor.logs"


class ServerAction(models.Model):
    _inherit = "ir.actions.server"

    def run(self):
        if len(self) > 1:
            res = False
            for action in self:
                res = action.run()
            return res
        start = time.perf_counter()
        try:
            res = super().run()
        except Exception:
            self._monitor_log(time.perf_counter() - start, traceback.format_exc())
            raise
        self._monitor_log(time.perf_counter() - start)
        return res

    def _monitor_log(self, duration, exception=None):
        """Buffer the execution in memory, without touching the database.

        The buffer is written once the current transaction is over (committed
        or rolled back), in a new short transaction. Writing it from a second
        cursor while the current transaction still holds its locks is what
        caused the deadlocks in the past: the current transaction waits for the
        second one, which may wait for a lock of the current one, and
        PostgreSQL can't detect it.
        """
        if not self:
            return
        cr = self.env.cr
        buffer = cr.postcommit.data.get(BUFFER_KEY)
        if buffer is None:
            buffer = {"runs": {}, "errors": []}
            # A transaction ends either with a commit or a rollback: the hook of
            # the other one is discarded, so the buffer is written only once.
            cr.postcommit.data[BUFFER_KEY] = buffer
            flush = self._monitor_flush_callback(buffer)
            cr.postcommit.add(flush)
            cr.postrollback.add(flush)
        if exception:
            buffer["errors"].append((self.id, self.env.uid, duration, exception))
        else:
            run = buffer["runs"].setdefault((self.id, self.env.uid), [0, 0.0, 0.0])
            run[0] += 1
            run[1] += duration
            run[2] = max(run[2], duration)

    def _monitor_flush_callback(self, buffer):
        registry = self.env.registry

        def flush():
            rows = [
                (action_id, uid, count, total, longest, None)
                for (action_id, uid), (count, total, longest) in buffer["runs"].items()
            ] + [
                (action_id, uid, 1, duration, duration, exception)
                for action_id, uid, duration, exception in buffer["errors"]
            ]
            if not rows:
                return
            try:
                with registry.cursor() as cr:
                    self.env(cr=cr, su=True)["server.action.monitor"]._insert_logs(rows)
            except Exception:
                # Monitoring must never break or block the business process
                _logger.warning(
                    "Could not save server actions monitoring", exc_info=True
                )

        return flush

    def action_open_monitor_logs(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "base_cron_monitor.action_server_action_monitor"
        )
        action["domain"] = [("server_action_id", "in", self.ids)]
        return action
