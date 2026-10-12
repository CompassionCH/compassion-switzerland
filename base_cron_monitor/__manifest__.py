# Copyright 2024 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Monitor Scheduled and Automated Actions",
    "summary": "Monitor Scheduled and Automated Actions",
    "version": "18.0.1.0.0",
    # see https://odoo-community.org/page/development-status
    "development_status": "Beta",
    "category": "Tools",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "author": "Compassion CH",
    "maintainers": ["ecino"],
    "license": "AGPL-3",
    "installable": True,
    "data": [
        "security/ir.model.access.csv",
        "views/server_action_monitor.xml",
    ],
    "depends": [
        "base_automation",
    ],
}
