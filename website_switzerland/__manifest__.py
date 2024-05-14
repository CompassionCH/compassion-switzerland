##############################################################################
#
#    Copyright (C) 2023 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
# pylint: disable=C8101
{
    "name": "Website - Compassion Switzerland custom views",
    "version": "14.0.1.0.0",
    "category": "Website",
    "author": "Compassion Switzerland",
    "development_status": "Beta",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": [
        "my_compassion_segmentation",
        "theme_compassion",
        "partner_communication_switzerland",
        "website_crm_request",
        "website_event_compassion",
        "partner_segmentation",
    ],
    "data": [
        "data/group_visit_emails.xml",
        "data/communication_config.xml",
        "data/event_registration_stage.xml",
        "data/survey.xml",
        "data/event_type.xml",
        "data/event_type_mail.xml",
        "data/event_registration_task.xml",
        "data/res_lang.xml",
        "data/website_rewrite.xml",
        "data/website_menu.xml",
        "templates/footer.xml",
        "templates/contact_us.xml",
    ],
    "installable": True,
    "auto_install": False,
}
