##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    @classmethod
    def _get_translation_frontend_modules_name(cls):
        """Serve this module's JavaScript translations to the website.

        The website only sends the browser the translations of the modules
        listed here (website adds every installed module whose name starts
        with "website"), so the _t() strings of this module's frontend
        scripts would otherwise stay in English.
        """
        mods = super()._get_translation_frontend_modules_name()
        return mods + ["my_compassion_switzerland"]
