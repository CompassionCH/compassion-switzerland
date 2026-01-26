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
    "version": "14.0.1.0.1",
    "category": "Website",
    "author": "Daniel Palumbo",
    "development_status": "Beta",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "depends": [
        "my_compassion",
        "theme_compassion_2025",
        "partner_compassion",
        "ebill_postfinance_recipient_subscription",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/access_rules.xml",
        "data/account_payment_mode_data.xml",
        "data/product_funds_data.xml",
        "views/advocate_engagement_view.xml",
        "templates/components/volunteering_card.xml",
        "templates/my2_volunteering.xml",
        "views/advocate_engagement_notification_settings_view.xml",
        "templates/my2_new_sponsorship_wizard_ebill.xml",
        "templates/assets.xml",
        "data/engagement_types_data.xml",
    ],
    "installable": True,
    "auto_install": False,
}
