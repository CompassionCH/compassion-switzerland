from odoo import fields, models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    mailchimp_template_ids = fields.One2many(
        "mailchimp.email.lang.template", "email_template_id", "Mailchimp templates"
    )
