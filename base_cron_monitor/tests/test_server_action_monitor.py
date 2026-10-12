# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase


class TestServerActionMonitor(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # The logs are written with a new cursor: keep it in the test transaction
        cls.registry.enter_test_mode(cls.cr)
        cls.addClassCleanup(cls.registry.leave_test_mode)
        model = cls.env.ref("base.model_res_partner")
        cls.action = cls.env["ir.actions.server"].create(
            {"name": "Monitored", "model_id": model.id, "state": "code", "code": "1"}
        )
        cls.failing_action = cls.env["ir.actions.server"].create(
            {
                "name": "Failing",
                "model_id": model.id,
                "state": "code",
                "code": "raise UserError('Boom')",
            }
        )
        cls.Monitor = cls.env["server.action.monitor"]

    def _logs(self, action):
        return self.Monitor.search([("server_action_id", "=", action.id)])

    def test_logs_after_commit(self):
        self.action.run()
        self.action.run()
        # Nothing is written while the transaction is running
        self.assertFalse(self._logs(self.action))

        self.env.cr.postcommit.run()
        log = self._logs(self.action)
        self.assertEqual(len(log), 1)
        self.assertEqual(log.run_count, 2)
        self.assertEqual(log.user_id, self.env.user)
        self.assertEqual(log.usage, "ir_actions_server")
        self.assertGreaterEqual(log.duration, log.max_duration)
        self.assertFalse(log.exception)

    def test_logs_after_rollback(self):
        self.action.run()
        with self.assertRaises(UserError):
            self.failing_action.run()
        # Simulate the rollback of the transaction
        self.env.cr.postcommit.clear()
        self.env.cr.postrollback.run()

        self.assertEqual(self._logs(self.action).run_count, 1)
        error = self._logs(self.failing_action)
        self.assertEqual(len(error), 1)
        self.assertIn("Boom", error.exception)

    def test_logs_of_cron(self):
        cron = self.env["ir.cron"].create(
            {
                "name": "Monitored cron",
                "model_id": self.env.ref("base.model_res_partner").id,
                "state": "code",
                "code": "1",
            }
        )
        cron.method_direct_trigger()
        self.env.cr.postcommit.run()
        self.assertEqual(self._logs(cron.ir_actions_server_id).usage, "ir_cron")

    def test_autovacuum(self):
        self.action.run()
        self.env.cr.postcommit.run()
        log = self._logs(self.action)
        self.env.cr.execute(
            "UPDATE server_action_monitor SET create_date = %s WHERE id = %s",
            (fields.Datetime.now() - timedelta(days=31), log.id),
        )
        self.Monitor._gc_monitor_logs()
        self.assertFalse(log.exists())
