# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class QualityTestCategory(models.Model):
    _name = "quality.test.category"
    _description = "Quality Test Category"
    _order = "name"

    name = fields.Char(required=True)
    parent_id = fields.Many2one(
        "quality.test.category",
        string="Parent Category",
        ondelete="set null",
    )

    @api.depends("name", "parent_id")
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = rec._get_full_name()

    def _get_full_name(self):
        """Return the complete category path."""
        self.ensure_one()
        if self.parent_id:
            return f"{self.parent_id._get_full_name()} / {self.name}"
        return self.name
