# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monitor Scheduled and Automated Actions",
    "summary": "Monitor Scheduled and Automated Actions",
    "version": "14.0.1.0.0",
    # see https://odoo-community.org/page/development-status
    "development_status": "Beta",
    "category": "Tools",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "author": "Compassion Switzerland",
    "maintainers": ["ecino"],
    "license": "AGPL-3",
    "installable": True,
    "data": [
        "views/ir_cron_view.xml",
        "views/base_automation_view.xml",
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "base_automation",
        "queue_job",
    ],
}
