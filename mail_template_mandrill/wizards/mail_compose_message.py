from odoo import models
from odoo.tools.safe_eval import safe_eval


class EmailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def get_mail_values(self, res_ids):
        """Attach mailchimp template to e-mail (in SMTP headers)"""
        mail_values = super().get_mail_values(res_ids)
        template = self.template_id
        mailchimp_template = template.mailchimp_template_ids.filtered(
            lambda m: m.lang == self.env.lang
        )

        if mailchimp_template:
            for message_vals in mail_values.values():
                headers = safe_eval(message_vals.get("headers", "{}"))
                headers.update({"X-MC-Template": mailchimp_template.mailchimp_template})
                message_vals["headers"] = headers

        return mail_values
