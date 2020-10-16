from odoo import models, api
from odoo.tools.safe_eval import safe_eval


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.multi
    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, body='', subject=None,
                     message_type='notification', subtype=None,
                     parent_id=False, attachments=None,
                     notif_layout=False, add_sign=True, model_description=False,
                     mail_auto_delete=True, **kwargs):
        # Put headers in context to force pushing them in mails created.
        new_self = self
        headers = kwargs.get("headers")
        if headers:
            new_self = self.with_context(default_headers=headers)
        return super(MailThread, new_self).message_post(
            body=body, subject=subject, message_type=message_type, subtype=subtype,
            parent_id=parent_id, attachments=attachments, notif_layout=notif_layout,
            add_sign=add_sign, model_description=model_description,
            mail_auto_delete=mail_auto_delete, **kwargs)

    @api.multi
    def _notify_specific_email_values(self, message):
        """ Get specific notification email values to store on the notification
        mail.mail. Override to add values related to a specific model.

        :param message: mail.message record being notified by email
        """
        res = super()._notify_specific_email_values(message)
        default_headers = self.env.context.get("default_headers")
        if default_headers:
            default_headers.update(safe_eval(res.get("headers", "{}")))
            res["headers"] = default_headers
        return res
