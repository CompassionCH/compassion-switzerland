##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
# pylint: disable=C8101
{
    "name": "My Compassion Switzerland",
    "version": "14.0.1.0.0",
    "category": "Website",
    "author": "Daniel Palumbo",
    "development_status": "Beta",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "depends": [
        "message_center_compassion",
        "my_compassion",
        "theme_compassion_2025",
        "partner_compassion",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/access_rules.xml",
        "views/advocate_engagement_view.xml",

        "templates/components/volunteering_card.xml",
        "templates/my2_volunteering.xml",
        "views/advocate_engagement_notification_settings_view.xml",
    ],
    "installable": True,
    "auto_install": False,
}
