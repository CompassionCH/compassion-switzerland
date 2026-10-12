# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, new_test_user

from ..models.automation_simulate_target import ENABLED_PARAM, WIZARD_MODEL


class TestAutomationSimulate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env, login="simulate_user", groups="base.group_user"
        )
        cls.partners = cls.env["res.partner"].create(
            [{"name": "Simulate 1"}, {"name": "Simulate 2"}]
        )
        model = cls.env.ref("base.model_res_partner")
        cls.automation = cls.env["base.automation"].create(
            {
                "name": "Simulated rule",
                "trigger": "on_time",
                "model_id": model.id,
                "trg_date_range": 10,
                "trg_date_range_type": "day",
                "trg_date_id": cls.env.ref("base.field_res_partner__write_date").id,
            }
        )
        action = cls.env["ir.actions.server"].create(
            {
                "name": "Write comment",
                "base_automation_id": cls.automation.id,
                "model_id": model.id,
                "state": "code",
                "code": "record.write({'comment': 'automation'})",
            }
        )
        cls.automation.write({"action_server_ids": [Command.link(action.id)]})
        cls.cron = cls.env["ir.cron"].create(
            {
                "name": "Simulated cron",
                "model_id": model.id,
                "state": "code",
                "code": "model.search([('name', '=like', 'Simulate %')])"
                ".write({'comment': 'cron'})",
                "interval_number": 1,
                "interval_type": "days",
            }
        )

    def _bindings(self):
        return self.env["ir.actions.act_window"].search(
            [("res_model", "=", WIZARD_MODEL)]
        )

    def _target(self, record):
        field = "automation_id" if record._name == "base.automation" else "cron_id"
        return self.env["automation.simulate.target"].search([(field, "=", record.id)])

    def _wizard(self, kind, record):
        self.env["ir.config_parameter"].set_param(ENABLED_PARAM, True)
        return (
            self.env[WIZARD_MODEL]
            .with_user(self.user)
            .with_context(active_model="res.partner", active_ids=self.partners.ids)
            .create({"kind": kind, "target_id": self._target(record).id})
        )

    def test_enable_disable(self):
        self.env["ir.config_parameter"].set_param(ENABLED_PARAM, False)
        self.assertFalse(self._bindings())
        self.assertFalse(self._target(self.automation))

        self.env["ir.config_parameter"].set_param(ENABLED_PARAM, True)
        self.assertIn(
            self.env.ref("base.model_res_partner"), self._bindings().binding_model_id
        )
        self.assertTrue(self._target(self.automation))
        self.assertTrue(self._target(self.cron))

        self.automation.active = False
        self.assertFalse(self._target(self.automation))

        self.env["ir.config_parameter"].set_param(ENABLED_PARAM, False)
        self.assertFalse(self._bindings())
        self.assertFalse(self.env["automation.simulate.target"].search([]))

    def test_simulate_automation(self):
        wizard = self._wizard("automation", self.automation)
        self.assertEqual(wizard.record_count, 2)
        wizard.action_simulate()
        self.assertEqual(set(self.partners.mapped("comment")), {"automation"})

    def test_simulate_cron(self):
        self._wizard("cron", self.cron).action_simulate()
        self.assertEqual(set(self.partners.mapped("comment")), {"cron"})

    def test_disabled(self):
        wizard = self._wizard("automation", self.automation)
        self.env["ir.config_parameter"].set_param(ENABLED_PARAM, False)
        with self.assertRaises(UserError):
            wizard.action_simulate()
