# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QualityTestModuleVersion(models.Model):
    _name = "quality.test.module.version"
    _description = "Quality Test Module Version Snapshot"
    _order = "module_id"

    run_id = fields.Many2one(
        "quality.test.run",
        string="Test Run",
        required=True,
        ondelete="cascade",
        index=True,
    )
    module_id = fields.Many2one(
        "ir.module.module",
        string="Module",
        required=True,
        ondelete="cascade",
    )
    version = fields.Char(
        string="Version at Test Time",
        required=True,
    )
    current_version = fields.Char(
        string="Current Version",
        compute="_compute_current_version",
    )
    version_changed = fields.Boolean(
        string="Version Changed",
        compute="_compute_current_version",
        help="True if the module version has changed since this test run.",
    )

    def _compute_current_version(self):
        for rec in self:
            current = rec.module_id.installed_version or ""
            rec.current_version = current
            rec.version_changed = bool(current) and current != rec.version
