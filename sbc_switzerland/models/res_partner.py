from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def agree_to_child_protection_charter(self):
        res = super().agree_to_child_protection_charter()
        job_delay = datetime.now() + relativedelta(days=7)
        for partner in self:
            translator = (
                self.env["translation.user"]
                .sudo()
                .search(
                    [
                        ("partner_id", "=", partner.id),
                    ]
                )
            )
            if translator:
                partner.sudo().with_delay(eta=job_delay).welcome_translator()
        return res

    def welcome_translator(self):
        self.ensure_one()
        translator_welcome = self.env.ref("sbc_switzerland.new_translator_welcome")
        self.env["partner.communication.job"].create(
            {
                "config_id": translator_welcome.id,
                "partner_id": self.id,
                "object_ids": self.id,
            }
        ).send()
