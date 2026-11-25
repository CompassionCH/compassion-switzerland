# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models

ENABLED_PARAM = "automation_simulate.enabled"
WIZARD_MODEL = "automation.simulate.wizard"


class AutomationSimulateTarget(models.Model):
    """Automation rule or scheduled action that can be simulated.

    Mirrors the active base.automation and ir.cron records, which only
    administrators can read, so that every user can select them in the
    simulation wizard. Kept in sync by ``_sync``.
    """

    _name = "automation.simulate.target"
    _description = "Simulation target"
    _order = "kind, name"

    name = fields.Char(required=True, readonly=True)
    kind = fields.Selection(
        [("automation", "Automation rule"), ("cron", "Scheduled action")],
        required=True,
        readonly=True,
    )
    model_id = fields.Many2one(
        "ir.model", required=True, readonly=True, ondelete="cascade"
    )
    model = fields.Char(related="model_id.model", store=True, index=True)
    automation_id = fields.Many2one(
        "base.automation", readonly=True, ondelete="cascade"
    )
    cron_id = fields.Many2one("ir.cron", readonly=True, ondelete="cascade")

    @api.model
    def _is_enabled(self):
        value = self.env["ir.config_parameter"].sudo().get_param(ENABLED_PARAM)
        return str(value).lower() in ("1", "true", "yes")

    @api.model
    def _sync(self):
        """Mirror the active automation rules and scheduled actions, and bind
        the simulation wizard to their models. Remove everything when the
        feature is disabled."""
        wanted = {}
        if self._is_enabled():
            for automation in (
                self.env["base.automation"].sudo().search([("active", "=", True)])
            ):
                wanted[("automation", automation.id)] = {
                    "name": automation.name,
                    "kind": "automation",
                    "model_id": automation.model_id.id,
                    "automation_id": automation.id,
                }
            for cron in self.env["ir.cron"].sudo().search([("active", "=", True)]):
                wanted[("cron", cron.id)] = {
                    "name": cron.name,
                    "kind": "cron",
                    "model_id": cron.model_id.id,
                    "cron_id": cron.id,
                }

        targets = self.sudo().search([])
        obsolete = targets.browse()
        for target in targets:
            res_id = target.automation_id.id or target.cron_id.id
            vals = wanted.pop((target.kind, res_id), None)
            if vals is None:
                obsolete |= target
            elif (target.name, target.model_id.id) != (vals["name"], vals["model_id"]):
                target.write({"name": vals["name"], "model_id": vals["model_id"]})
        obsolete.unlink()
        self.sudo().create(list(wanted.values()))
        self._sync_bindings()

    @api.model
    def _sync_bindings(self):
        """Add the "Simulate process" action on the models having targets."""
        actions = (
            self.env["ir.actions.act_window"]
            .sudo()
            .search([("res_model", "=", WIZARD_MODEL)])
        )
        missing_models = self.sudo().search([]).model_id
        obsolete = actions.browse()
        for action in actions:
            if action.binding_model_id in missing_models:
                missing_models -= action.binding_model_id
            else:
                obsolete |= action
        obsolete.unlink()
        actions.create(
            [
                {
                    "name": self.env._("Simulate process"),
                    "res_model": WIZARD_MODEL,
                    "view_mode": "form",
                    "target": "new",
                    "binding_model_id": model.id,
                    "binding_view_types": "list,form",
                }
                for model in missing_models
            ]
        )
