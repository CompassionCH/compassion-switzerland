# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Quality Test Management",
    "summary": "Define quality tests for critical processes and track test runs",
    "version": "18.0.1.0.0",
    "development_status": "Beta",
    "category": "Quality",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "author": "Compassion CH",
    "maintainers": ["ecino"],
    "license": "AGPL-3",
    "installable": True,
    "depends": [
        "base",
        "hr",
        "mail",
        "project",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/quality_test_category_data.xml",
        "data/mail_template_quality_test.xml",
        "data/quality_test_cron.xml",
        "views/project_task_views.xml",
        "views/quality_test_views.xml",
        "views/quality_test_run_views.xml",
    ],
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
}
