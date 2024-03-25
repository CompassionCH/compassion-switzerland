# Copyright 2018-2023 CompassionCH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Mail activity to CRM request",
    "summary": "Enable to convert activities to CRM requests",
    "version": "14.0.1.0.0",
    "development_status": "Beta",
    "category": "Helpdesk",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "author": "Compassion Switzerland",
    "maintainers": ["ecino"],
    "license": "AGPL-3",
    "installable": True,
    "external_dependencies": {"python": ["pandas>=1.5.3"]},
    "depends": [
        "crm_request",
    ],
    "data": [
        "views/mail_activity_views.xml",
        "data/claim_sequence.xml",
    ],
}
