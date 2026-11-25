# Copyright 2026 Compassion CH (http://www.compassion.ch)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models

# Models whose records follow their manual distribution: the ones that give a
# distribution to future entries (employee contracts, assets, asset profiles),
# never the journal items already posted.
SYNC_MODELS = ["hr.contract", "account.asset", "account.asset.profile"]


class AccountAnalyticDistributionManual(models.Model):
    _inherit = "account.analytic.distribution.manual"

    @api.model
    def _get_sync_models(self):
        return [
            model
            for model in SYNC_MODELS
            if model in self.env and "manual_distribution_id" in self.env[model]._fields
        ]

    def write(self, vals):
        res = super().write(vals)
        if "analytic_distribution" in vals:
            self._sync_distribution()
        return res

    def _sync_distribution(self):
        """Give the distribution of each manual distribution to the records
        that use it."""
        for model in self._get_sync_models():
            records = (
                self.env[model]
                .with_context(active_test=False)
                .search([("manual_distribution_id", "in", self.ids)])
            )
            for distribution, group in records.grouped(
                "manual_distribution_id"
            ).items():
                group.write(
                    {"analytic_distribution": distribution.analytic_distribution}
                )
