# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from contextlib import contextmanager
from unittest.mock import patch

from odoo import SUPERUSER_ID, api
from odoo.exceptions import UserError
from odoo.modules.registry import Registry
from odoo.tests import BaseCase, tagged
from odoo.tests.common import get_db_name


@tagged("post_install", "-at_install")
class TestServerActionMonitorConcurrency(BaseCase):
    """Run the actions in real and independent transactions, really committed
    or rolled back, to check that the logs are only written once the monitored
    transaction is over and has released its locks.

    The data is committed in the database and removed at the end.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.registry = Registry(get_db_name())
        with cls._env() as env:
            model = env.ref("base.model_res_partner")
            actions = env["ir.actions.server"].create(
                [
                    {
                        "name": "Monitored (concurrency test)",
                        "model_id": model.id,
                        "state": "code",
                        "code": "1",
                    },
                    {
                        "name": "Failing (concurrency test)",
                        "model_id": model.id,
                        "state": "code",
                        "code": "raise UserError('Boom')",
                    },
                ]
            )
            cls.action_id, cls.failing_action_id = actions.ids
        cls.addClassCleanup(cls._remove_actions)

    @classmethod
    def _remove_actions(cls):
        with cls._env() as env:
            env["ir.actions.server"].browse(
                [cls.action_id, cls.failing_action_id]
            ).unlink()

    @classmethod
    @contextmanager
    def _env(cls):
        with cls.registry.cursor() as cr:
            yield api.Environment(cr, SUPERUSER_ID, {})

    def setUp(self):
        super().setUp()
        with self.registry.cursor() as cr:
            cr.execute(
                "DELETE FROM server_action_monitor WHERE server_action_id IN %s",
                [(self.action_id, self.failing_action_id)],
            )

    def _monitored_cursor(self):
        cr = self.registry.cursor()
        cr.execute("SELECT pg_backend_pid()")
        self.monitored_pid = cr.fetchone()[0]
        return cr

    @contextmanager
    def _spy_insert(self):
        """Record, for each insert of logs, if the monitored transaction was
        still open at that time."""
        model = self.registry["server.action.monitor"]
        insert = model._insert_logs
        inserts = []

        def spy(monitor, rows):
            monitor.env.cr.execute(
                "SELECT xact_start IS NOT NULL FROM pg_stat_activity WHERE pid = %s",
                [self.monitored_pid],
            )
            inserts.append(monitor.env.cr.fetchone()[0])
            return insert(monitor, rows)

        with patch.object(model, "_insert_logs", spy):
            yield inserts

    def _run(self, cr, action_id):
        api.Environment(cr, SUPERUSER_ID, {})["ir.actions.server"].browse(
            action_id
        ).run()

    def _logs(self, action_id):
        """Read the logs from an independent transaction."""
        with self.registry.cursor() as cr:
            cr.execute(
                "SELECT run_count, exception FROM server_action_monitor "
                "WHERE server_action_id = %s",
                [action_id],
            )
            return cr.fetchall()

    def test_logs_written_after_commit(self):
        with self._spy_insert() as inserts, self._monitored_cursor() as cr:
            # Lock the action like a concurrent edit would. The insert of the
            # log references it (foreign key), so writing the log while this
            # transaction runs would wait for the lock: this froze v14.
            cr.execute(
                "SELECT id FROM ir_act_server WHERE id = %s FOR UPDATE",
                [self.action_id],
            )
            self._run(cr, self.action_id)
            self._run(cr, self.action_id)
            self.assertEqual(inserts, [])
            self.assertEqual(self._logs(self.action_id), [])
        # The cursor is committed when leaving the block
        self.assertEqual(inserts, [False], "Logs written in an open transaction")
        self.assertEqual(self._logs(self.action_id), [(2, None)])

    def test_logs_survive_rollback(self):
        with self._spy_insert() as inserts, self._monitored_cursor() as cr:
            cr.execute(
                "SELECT id FROM ir_act_server WHERE id IN %s FOR UPDATE",
                [(self.action_id, self.failing_action_id)],
            )
            self._run(cr, self.action_id)
            with self.assertRaises(UserError):
                self._run(cr, self.failing_action_id)
            cr.rollback()
            self.assertEqual(inserts, [False], "Logs written in an open transaction")
        self.assertEqual(self._logs(self.action_id), [(1, None)])
        [(run_count, exception)] = self._logs(self.failing_action_id)
        self.assertEqual(run_count, 1)
        self.assertIn("Boom", exception)

    def test_logs_survive_closed_cursor(self):
        """The cursor is closed without commit, like after a failing request."""
        with self._spy_insert() as inserts:
            with self.assertRaises(UserError), self._monitored_cursor() as cr:
                self._run(cr, self.failing_action_id)
        self.assertEqual(inserts, [False], "Logs written in an open transaction")
        self.assertEqual(len(self._logs(self.failing_action_id)), 1)
