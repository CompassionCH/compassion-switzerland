# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
# pylint: disable=C8101
{
    "name": "Simulate automations",
    "summary": "Run automation rules and scheduled actions on demand for testing",
    "author": "Compassion CH",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "license": "AGPL-3",
    "category": "Technical",
    "version": "18.0.1.0.0",
    "depends": [
        "base_automation",
        "base_setup",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "wizards/automation_simulate_wizard_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
}
