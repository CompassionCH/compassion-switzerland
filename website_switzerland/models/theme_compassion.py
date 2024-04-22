from odoo import models


class ThemeCompassion(models.AbstractModel):
    _inherit = "theme.utils"

    def _theme_compassion_post_copy(self, mod):
        super()._theme_compassion_post_copy(mod)
        self.disable_view("website.template_footer_call_to_action")
        self.enable_view("website_switzerland.footer")
