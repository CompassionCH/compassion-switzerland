from odoo import models, fields, exceptions , api


class AdvocateEngagementNotificationSettings(models.TransientModel):
    _inherit = "res.config.settings"
    help_field_template = "Email address to notify when an advocates engagement form is submitted in "

    advocate_engagement_notify_fr_email = fields.Char(
        "Adv. engagement (FR)",
        config_parameter="partner_communication_switzerland.advocate_engagement_notify_fr_email",
        default="site_fr_participate@compassion.ch",
        help=f"{help_field_template}French."
    )
    advocate_engagement_notify_de_email = fields.Char(
        "Adv. engagement (DE)",
        config_parameter="partner_communication_switzerland.advocate_engagement_notify_de_email",
        default="site_it_participate@compassion.ch",
        help=f"{help_field_template}French."
    )
    advocate_engagement_notify_it_email = fields.Char(
        "Adv. engagement (IT)",
        config_parameter="partner_communication_switzerland.advocate_engagement_notify_it_email",
        default="site_it_participate@compassion.ch",
        help=f"{help_field_template}French."
    )
    advocate_engagement_notify_default_email = fields.Char(
        "Advocate engagement (Default)",
        config_parameter="partner_communication_switzerland.advocate_engagement_notify_default_email",
        default = "site_de_participate@compassion.ch",
        help=f"{help_field_template} any other languages than german, french and italian."
    )


    def _is_valid_email(self, email):
        """Validates the email format. Returns True if the format is respected."""
        import re
        if not email:
            return False
        pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        return bool(pattern.match(email))

    def set_values(self):

        emails = {
            "advocate_engagement_notify_fr_email": self.advocate_engagement_notify_fr_email,
            "advocate_engagement_notify_de_email": self.advocate_engagement_notify_de_email,
            "advocate_engagement_notify_it_email": self.advocate_engagement_notify_it_email,
            "advocate_engagement_notify_default_email": self.advocate_engagement_notify_default_email,
        }
        for field_name, value in emails.items():
            if not value:
                continue
            if not self._is_valid_email(value.strip()):
                raise exceptions.ValidationError(
                    "Invalid email for %s: %s" % (field_name, value)
                )
        return super().set_values()

    @api.model
    def get_advocate_engagement_recipients(self):
        """
        Fetches the advocate engagement notification emails from system settings.

        Returns:
            dict: A dictionary mapping language codes ('fr', 'de', 'it', 'default')
                  to their respective recipient email addresses.
        """
        ICP = self.env['ir.config_parameter'].sudo()

        field_map = {
                   'fr': 'advocate_engagement_notify_fr_email',
                   'de': 'advocate_engagement_notify_de_email',
                   'it': 'advocate_engagement_notify_it_email',
                   'default': 'advocate_engagement_notify_default_email',
               }

        recipients = {}
        for lang, field in field_map.items():
            param_key = self._fields[field].config_parameter
            value = ICP.get_param(param_key, default='')
            recipients[lang] = value

        return recipients