from odoo import models
from odoo.tools.safe_eval import safe_eval


class CommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    def _send_mail_asynchronous(self):
        """Attach the mandrill template to the e-mail (in SMTP headers).
        Jobs create the mail.mail directly, without the mail composer.
        """
        self.ensure_one()
        mandrill_template = self.email_template_id.mailchimp_template_ids.filtered(
            lambda m: m.lang == self.partner_id.lang
        )[:1]
        if mandrill_template and not self.email_id:
            email_vals = dict(self.env.context.get("default_email_vals", {}))
            headers = safe_eval(email_vals.get("headers") or "{}")
            headers["X-MC-Template"] = mandrill_template.mailchimp_template
            email_vals["headers"] = repr(headers)
            self = self.with_context(default_email_vals=email_vals)
        return super()._send_mail_asynchronous()
