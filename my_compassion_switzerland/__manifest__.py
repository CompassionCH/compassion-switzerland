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
    "version": "18.0.1.0.0",
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
        "sponsorship_switzerland",
        "crowdfunding_compassion",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/access_rules.xml",
        "data/account_payment_mode_data.xml",
        "data/product_funds_data.xml",
        "data/product_gifts_data.xml",
        "data/engagement_types_data.xml",
        "data/mail_template_data.xml",
        "views/advocate_engagement_view.xml",
        "templates/my2_dashboard.xml",
        "templates/components/volunteering_card.xml",
        "templates/my2_volunteering.xml",
        "views/advocate_engagement_notification_settings_view.xml",
        "templates/my2_new_sponsorship_wizard_ebill.xml",
        "templates/my_account_menu.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "my_compassion_switzerland/static/src/css/my2_volunteering.css",
            "my_compassion_switzerland/static/src/js/my2_volunteering.js",
        ],
    },
    "installable": True,
    "auto_install": False,
}
