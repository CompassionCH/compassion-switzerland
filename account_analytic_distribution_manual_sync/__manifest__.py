# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Analytic Manual Distributions - Keep In Sync",
    "summary": "A change of a manual distribution goes to the contracts and assets "
    "that use it",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "category": "Accounting",
    "author": "Compassion CH",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "depends": ["account_analytic_distribution_manual"],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
