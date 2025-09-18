from odoo import models, fields, exceptions


class AdvocateEngagementNotificationSettings(models.TransientModel):
    _inherit = "res.config.settings"

    advocate_engagement_notify_fr_email = fields.Char(
        "Adv. engagement (FR)",
        config_parameter="partner_communication_switzerland.advocate_engagement_notify_fr_email",
        default="site_fr_participate@compassion.ch"
    )
    advocate_engagement_notify_de_email = fields.Char(
        "Adv. engagement (DE)",
        config_parameter="partner_communication_switzerland.advocate_engagement_notify_de_email",
        default="site_it_participate@compassion.ch"
    )
    advocate_engagement_notify_it_email = fields.Char(
        "Adv. engagement (IT)",
        config_parameter="partner_communication_switzerland.advocate_engagement_notify_it_email",
        default="site_it_participate@compassion.ch"
    )
    advocate_engagement_notify_default_email = fields.Char(
        "Advocate engagement (Default)",
        config_parameter="partner_communication_switzerland.advocate_engagement_notify_default_email",
        default = "site_de_participate@compassion.ch"
    )

    def _is_valid_email(self, email):
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