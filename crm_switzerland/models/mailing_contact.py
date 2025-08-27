from odoo import models


class MailingContact(models.Model):
    _inherit = "mailing.contact"

    def _get_global_dict(self):
        res = super()._get_global_dict()
        res.update(
            {
                "partner": self.partner_id,
            }
        )
        return res
