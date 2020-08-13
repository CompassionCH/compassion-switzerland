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
        if not action.config_id or not self._context.get('active_id') or self._is_recompute(action):
            return False

        comm_job = self.env["partner.communication.job"]
        communications = self.env["partner.communication.job"]
        if "records" in eval_context:
            for record in eval_context["records"]:
                partner_id = record.mapped(action.partner_field)
                vals = {
                    "partner_id": partner_id.id,
                    "object_ids": record.id,
                    "config_id": action.config_id.id,
                    "auto_send": False,
                }
                communications += comm_job.create(vals)
            
            for communication in communications:
                communication.send()
        return False
