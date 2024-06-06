from odoo import fields, models


class LanguageTemplate(models.Model):
    _name = "mailchimp.email.lang.template"
    _description = "Mailchimp mail template"

    email_template_id = fields.Many2one("mail.template", "E-mail Template")
    lang = fields.Selection("_select_lang", "Language", required=True)
    mailchimp_template = fields.Char(help="Put the mandrill template name")

    def _select_lang(self):
        languages = self.env["res.lang"].search([])
        return [(language.code, language.name) for language in languages]
