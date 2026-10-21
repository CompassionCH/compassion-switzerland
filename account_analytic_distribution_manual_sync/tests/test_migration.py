# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import TransactionCase, tagged

from ..hooks import post_init_hook


@tagged("post_install", "-at_install")
class TestMigration(TransactionCase):
    """Migration of the analytic tags of 14.0, with the 14.0 tables made up."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        if "account.asset.profile" not in cls.env:
            cls.skipTest(cls, "account_asset_management is not installed")
        cr = cls.env.cr
        cr.execute("SELECT to_regclass('account_analytic_tag')")
        if cr.fetchone()[0]:
            cls.skipTest(cls, "a database migrated from 14.0 has the real tables")
        cr.execute(
            """CREATE TABLE account_analytic_tag (id serial PRIMARY KEY, name varchar);
               CREATE TABLE account_analytic_distribution (
                   id serial PRIMARY KEY, tag_id int, account_id int, percentage float);
               CREATE TABLE account_analytic_tag_account_asset_profile_rel (
                   account_asset_profile_id int, account_analytic_tag_id int)"""
        )
        plan = cls.env["account.analytic.plan"].create({"name": "Migration test keys"})
        account_obj = cls.env["account.analytic.account"]
        cls.adm = account_obj.create({"name": "Migration test ADM", "plan_id": plan.id})
        cls.fund = account_obj.create(
            {"name": "Migration test Fundraising", "plan_id": plan.id}
        )
        journal = cls.env["account.journal"].search([("type", "=", "general")], limit=1)
        expense = cls.env["account.account"].search(
            [("account_type", "=", "expense")], limit=1
        )
        asset_account = cls.env["account.account"].create(
            {
                "name": "Migration test assets",
                "code": "150098",
                "account_type": "asset_fixed",
            }
        )
        cls.profile = cls.env["account.asset.profile"].create(
            {
                "name": "Migration test profile",
                "account_asset_id": asset_account.id,
                "account_depreciation_id": asset_account.id,
                "account_expense_depreciation_id": expense.id,
                "journal_id": journal.id,
            }
        )

    def _tag(self, name, distribution=None):
        cr = self.env.cr
        cr.execute(
            "INSERT INTO account_analytic_tag (name) VALUES (%s) RETURNING id", (name,)
        )
        tag_id = cr.fetchone()[0]
        for account, percentage in (distribution or {}).items():
            cr.execute(
                """INSERT INTO account_analytic_distribution
                   (tag_id, account_id, percentage) VALUES (%s, %s, %s)""",
                (tag_id, account.id, percentage),
            )
        cr.execute(
            """INSERT INTO account_analytic_tag_account_asset_profile_rel
               (account_asset_profile_id, account_analytic_tag_id) VALUES (%s, %s)""",
            (self.profile.id, tag_id),
        )
        return tag_id

    def test_ordinary_tag_ignored(self):
        """A profile with an ordinary tag (lower id) and a key gets the key."""
        self._tag("Migration test ordinary")
        self._tag("Migration test key", {self.adm: 30.0, self.fund: 70.0})
        post_init_hook(self.env)
        self.assertEqual(self.profile.manual_distribution_id.name, "Migration test key")
        self.assertEqual(
            self.profile.analytic_distribution,
            {str(self.adm.id): 30.0, str(self.fund.id): 70.0},
        )

    def test_existing_key_with_other_percentages(self):
        """An existing key of the same name keeps its percentages; the tag
        gets its own key with its 14.0 percentages."""
        existing = self.env["account.analytic.distribution.manual"].create(
            {
                "name": "Migration test key",
                "analytic_distribution": {str(self.adm.id): 100.0},
            }
        )
        self._tag("Migration test key", {self.adm: 60.0, self.fund: 40.0})
        post_init_hook(self.env)
        self.assertEqual(existing.analytic_distribution, {str(self.adm.id): 100.0})
        key = self.profile.manual_distribution_id
        self.assertEqual(key.name, "Migration test key (14.0)")
        self.assertEqual(
            self.profile.analytic_distribution,
            {str(self.adm.id): 60.0, str(self.fund.id): 40.0},
        )

    def test_rerun_reuses_keys(self):
        self._tag("Migration test key", {self.adm: 30.0, self.fund: 70.0})
        post_init_hook(self.env)
        post_init_hook(self.env)
        keys = self.env["account.analytic.distribution.manual"].search(
            [("name", "like", "Migration test key")]
        )
        self.assertEqual(len(keys), 1)
