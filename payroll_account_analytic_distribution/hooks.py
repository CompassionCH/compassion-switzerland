# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

from odoo.addons.account_analytic_distribution_manual_sync.hooks import (
    get_tag_distributions,
)

_logger = logging.getLogger(__name__)


QUALITY_TEST = "Payroll: payslips and their analytic split"
QUALITY_TEST_DESCRIPTION = """
<p>The salaries of each employee are split among analytic accounts by the
analytic distribution of their contract (e.g. ADM 30 % / Fundraising 70 %).
Check it after each migration or update of the payroll modules.</p>
<ol>
<li>Open an active employee contract with an analytic distribution.</li>
<li>Generate and confirm a payslip for a test month (or a payslip batch).</li>
<li>Open the journal entry of the payslip: every income and expense line
(4xxx) carries the distribution of the contract; the balance sheet lines
(2xxx) carry none.</li>
<li>Check the analytic items of an expense line: one per account of the
distribution, with the amount split by its percentage.</li>
<li>Cancel the test payslip (its entry is reversed or deleted).</li>
</ol>
"""


def post_init_hook(env):
    _create_quality_test(env)
    _migrate_analytic_tags(env)


def _create_quality_test(env):
    """A quality test reminds to check the payroll split after each update of
    the payroll modules (quality_test_compassion, when installed)."""
    if "quality.test" not in env or env["quality.test"].search(
        [("name", "=", QUALITY_TEST)], limit=1
    ):
        return
    modules = env["ir.module.module"].search(
        [
            ("name", "in", ["payroll", "payroll_account", "hr_contract"]),
            ("state", "=", "installed"),
        ]
    ) | env["ir.module.module"].search(
        [("name", "=", "payroll_account_analytic_distribution")]
    )
    category = env.ref(
        "quality_test_compassion.quality_test_category_accounting",
        raise_if_not_found=False,
    )
    test = env["quality.test"].create(
        {
            "name": QUALITY_TEST,
            "description": QUALITY_TEST_DESCRIPTION,
            "category_id": category.id if category else False,
            "user_id": env.ref("base.user_admin").id,
            "module_ids": [(6, 0, modules.ids)],
            "rule_module_update": True,
        }
    )
    if "active" in dict(test._fields["state"].selection):
        test.state = "active"


def _migrate_analytic_tags(env):
    """Databases migrated from 14.0: an employee contract had an analytic tag
    (hr_contract.analytic_tag_id) whose distribution split the salaries. The
    contract gets the manual distribution made of that tag, kept in sync with it."""
    cr = env.cr
    cr.execute(
        """SELECT 1 FROM information_schema.columns
           WHERE table_name = 'hr_contract' AND column_name = 'analytic_tag_id'"""
    )
    if not cr.fetchone():
        return
    manuals = get_tag_distributions(env)
    cr.execute(
        """SELECT id, analytic_tag_id FROM hr_contract
           WHERE analytic_tag_id IS NOT NULL AND manual_distribution_id IS NULL"""
    )
    contracts = env["hr.contract"].with_context(active_test=False)
    count = 0
    for contract_id, tag_id in cr.fetchall():
        manual = manuals.get(tag_id)
        if manual:
            contracts.browse(contract_id).write(
                {
                    "manual_distribution_id": manual.id,
                    "analytic_distribution": manual.analytic_distribution,
                }
            )
            count += 1
    _logger.info("%s contracts get the manual distribution of their tag", count)
