from odoo import _, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_open_split_wizard(self):
        """Open the wizard allowing to split this entry into two entries."""
        self.ensure_one()
        return {
            "name": _("Split Journal Entry"),
            "type": "ir.actions.act_window",
            "res_model": "account.move.split.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_id": self.id},
        }
