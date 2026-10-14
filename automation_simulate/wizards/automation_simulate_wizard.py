# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AutomationSimulateWizard(models.TransientModel):
    _name = "automation.simulate.wizard"
    _description = "Simulate automation rules and scheduled actions"

    res_model = fields.Char(required=True)
    res_ids = fields.Char(help="Comma-separated ids of the selected records")
    record_count = fields.Integer(compute="_compute_record_count")
    kind = fields.Selection(
        [("automation", "Automation rule"), ("cron", "Scheduled action")],
        required=True,
        default="automation",
    )
    target_id = fields.Many2one(
        "automation.simulate.target",
        "Process",
        required=True,
        domain="[('model', '=', res_model), ('kind', '=', kind)]",
    )

    @api.model
    def default_get(self, fields_list):
        self._check_enabled()
        res = super().default_get(fields_list)
        context = self.env.context
        res["res_model"] = context.get("active_model")
        res["res_ids"] = ",".join(str(i) for i in context.get("active_ids") or [])
        return res

    @api.depends("res_ids")
    def _compute_record_count(self):
        for wizard in self:
            wizard.record_count = len(wizard._get_res_ids())

    @api.onchange("kind")
    def _onchange_kind(self):
        self.target_id = False

    def _get_res_ids(self):
        return [int(i) for i in (self.res_ids or "").split(",") if i]

    def _check_enabled(self):
        if not self.env["automation.simulate.target"]._is_enabled():
            raise UserError(
                self.env._(
                    "The simulation of automations is disabled on this database."
                )
            )

    def action_simulate(self):
        self.ensure_one()
        self._check_enabled()
        target = self.target_id.sudo()
        if target.model != self.res_model:
            raise UserError(self.env._("This process doesn't belong to this model."))

        if target.kind == "automation":
            records = (
                self.env[self.res_model].sudo().browse(self._get_res_ids()).exists()
            )
            if not records:
                raise UserError(self.env._("Select at least one record."))
            _logger.warning(
                "User %s simulates automation rule %r on %s",
                self.env.user.login,
                target.automation_id.name,
                records,
            )
            target.automation_id._process(records)
            message = self.env._(
                "Automation rule %(name)s ran on %(count)s record(s).",
                name=target.name,
                count=len(records),
            )
        else:
            _logger.warning(
                "User %s simulates scheduled action %r",
                self.env.user.login,
                target.cron_id.name,
            )
            target.cron_id.method_direct_trigger()
            message = self.env._("Scheduled action %(name)s ran.", name=target.name)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": "success",
                "title": self.env._("Simulation done"),
                "message": message,
                "next": {"type": "ir.actions.act_window_close"},
            },
        }
