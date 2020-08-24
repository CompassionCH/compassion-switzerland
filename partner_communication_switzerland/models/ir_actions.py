##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    state = fields.Selection(
        selection_add=[("communication", "Send Communication")]
    )
    config_id = fields.Many2one(
        "partner.communication.config", "Communication type", readonly=False,
        domain="[('model_id', '=', model_id)]",
    )
    partner_field = fields.Char(string="Partner field name")

    @api.model
    def run_action_communication(self, action, eval_context=None):
        if not action.config_id or not self._context.get('active_id') or \
                self._is_recompute(action):
            return False

        comm_job = self.env["partner.communication.job"]
        model_name = action.model_name
        if "records" in eval_context:
            for partner in eval_context["records"].mapped(action.partner_field):
                children = eval_context["records"]
                records = self.env[model_name].search([
                    (action.partner_field, "=", partner.id),
                    ("id", "in", children.ids)
                ])
                vals = {
                    "partner_id": partner.id,
                    "object_ids": records.ids,
                    "config_id": action.config_id.id,
                }
                comm_job.create(vals)
        return True
