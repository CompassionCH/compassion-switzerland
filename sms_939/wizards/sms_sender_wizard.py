from odoo import models, fields, api


class SmsSender(models.TransientModel):
    _inherit = 'sms.send_sms'

    sms_provider_id = fields.Many2one(
        'sms.provider', "SMS Provider",
        default=lambda self: self.env.ref('sms_939.large_account_id', False),
        readonly=False)

    @api.multi
    def action_send_sms(self):
        return super(SmsSender, self.with_context(
            sms_provider=self.sms_provider_id)).action_send_sms()
