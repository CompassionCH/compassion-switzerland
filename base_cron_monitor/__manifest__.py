# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monitor Scheduled and Automated Actions",
    "summary": "Monitor Scheduled and Automated Actions",
    "version": "14.0.2.0.0",
    # see https://odoo-community.org/page/development-status
    "development_status": "Beta",
    "category": "Tools",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "author": "Compassion Switzerland",
    "maintainers": ["ecino"],
    "license": "AGPL-3",
    'installable': False,
    "data": [
        "security/ir.model.access.csv",
        "views/server_action_monitor.xml",
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
