##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.my_compassion.controllers.my2_user_settings import (
    MyCompassionUserController,
)


class MyCompassionUserSettingsControllerSwitzerland(MyCompassionUserController):
    def _communication_allowed_fields(self):
        return super()._communication_allowed_fields() | {
            "opt_out",
            "tax_certificate",
            "birthday_reminder",
            "sponsorship_anniversary_card",
        }
