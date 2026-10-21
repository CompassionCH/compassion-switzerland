# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Payroll Accounting - Analytic Distribution",
    "summary": "Split the salaries of an employee contract among analytic accounts",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "category": "Payroll",
    "author": "Compassion CH",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "depends": ["payroll_account", "account_analytic_distribution_manual_sync"],
    "data": ["views/hr_contract_views.xml"],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
