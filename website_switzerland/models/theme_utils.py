from odoo import models


class ThemeUtils(models.AbstractModel):
    _inherit = "theme.utils"

    def _theme_muskathlon_post_copy(self, mod):
        res = super()._theme_muskathlon_post_copy(mod)
        # Muskathlon sites keep an empty footer, without the Compassion CH
        # call to action block.
        self.disable_view("website_switzerland.footer")
        return res
