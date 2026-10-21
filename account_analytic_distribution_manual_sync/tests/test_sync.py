# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSync(TransactionCase):
    def test_profile_follows_manual_distribution(self):
        if "account.asset.profile" not in self.env:
            self.skipTest("account_asset_management is not installed")
        plan = self.env["account.analytic.plan"].create({"name": "Sync test keys"})
        account_obj = self.env["account.analytic.account"]
        adm = account_obj.create({"name": "Sync test ADM", "plan_id": plan.id})
        fund = account_obj.create({"name": "Sync test Fundraising", "plan_id": plan.id})
        manual = self.env["account.analytic.distribution.manual"].create(
            {"name": "Sync test key", "analytic_distribution": {str(adm.id): 100}}
        )
        journal = self.env["account.journal"].search(
            [("type", "=", "general")], limit=1
        )
        expense = self.env["account.account"].search(
            [("account_type", "=", "expense")], limit=1
        )
        asset_account = self.env["account.account"].search(
            [("account_type", "=", "asset_fixed")], limit=1
        ) or self.env["account.account"].create(
            {
                "name": "Sync test assets",
                "code": "150099",
                "account_type": "asset_fixed",
            }
        )
        profile = self.env["account.asset.profile"].create(
            {
                "name": "Sync test profile",
                "account_asset_id": asset_account.id,
                "account_depreciation_id": asset_account.id,
                "account_expense_depreciation_id": expense.id,
                "journal_id": journal.id,
                "manual_distribution_id": manual.id,
                "analytic_distribution": manual.analytic_distribution,
            }
        )
        other = profile.copy(
            {"name": "Sync test other", "manual_distribution_id": False}
        )
        new = {str(adm.id): 30.0, str(fund.id): 70.0}
        manual.analytic_distribution = new
        self.assertEqual(profile.analytic_distribution, new)
        self.assertEqual(other.analytic_distribution, {str(adm.id): 100})
