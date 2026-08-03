##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.my_compassion.controllers.my2_user import MyCompassionUserController


class MyCompassionUserControllerSwitzerland(MyCompassionUserController):
    def _get_vignettes(self, partner):
        vignettes = super()._get_vignettes(partner)
        vignettes.append(
            {
                "key": "volunteering",
                "template": "my_compassion_switzerland.dashboard_volunteering_vignette",
                "priority": 2 - partner.is_volunteer * 100,
            }
        )
        return sorted(vignettes, key=lambda v: v["priority"])
