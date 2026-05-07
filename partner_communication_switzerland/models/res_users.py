from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    def action_reset_password(self):
        create_mode = bool(self.env.context.get("create_user"))
        # Only override the rest behavior, not normal signup
        if create_mode:
            super().action_reset_password()
        else:
            self.mapped("partner_id").signup_prepare(
                signup_type="reset"
            )
            config = self.env.ref(
                "partner_communication_switzerland.reset_password_email"
            )
            for user in self:
                self.env["partner.communication.job"].create(
                    {
                        "partner_id": user.partner_id.id,
                        "config_id": config.id,
                        "auto_send": True,
                    }
                )
