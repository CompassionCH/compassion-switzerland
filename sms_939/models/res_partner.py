from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def message_post_send_sms(
        self, sms_message, numbers=None, partners=None, note_msg=None, log_error=False
    ):
        """Log SMS in separate object to use in Interaction Resume"""
        for partner in self:
            self.env["sms.log"].create(
                {"partner_id": partner.id, "text": sms_message, "subject": note_msg}
            )
        sms_id = self.env["sms.sms"].create(
            {
                "number": partner.mobile,
                "body": sms_message,
                "partner_id": partner.id,
            }
        )
        self.env["sms.api"]._send_sms_batch(
            [
                {
                    "number": partner.mobile,
                    "content": sms_message,
                    "res_id": sms_id.id,
                }
            ]
        )