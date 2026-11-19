from odoo import api, models


class Partner(models.Model):
    _inherit = "translation.user"

    @api.model_create_multi
    def create(self, vals_list):
        translators = super().create(vals_list)
        if not self.env.context.get("no_translator_invitation"):
            self.send_communication(
                self.env.ref("sbc_switzerland.new_translator_config")
            )
        return translators

    def toggle_active(self):
        res = super().toggle_active()
        self.send_communication(self.env.ref("sbc_switzerland.translator_goodbye"))
        return res

    def unlink(self):
        self.send_communication(self.env.ref("sbc_switzerland.translator_goodbye"))
        return super().unlink()

    def send_communication(self, config):
        for partner in self.mapped("partner_id"):
            self.env["partner.communication.job"].create(
                {
                    "partner_id": partner.id,
                    "config_id": config.id,
                    "object_ids": partner.id,
                }
            )
