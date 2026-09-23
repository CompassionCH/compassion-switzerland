# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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

    @api.depends("name", "parent_id.display_name")
    def _compute_display_name(self):
        """Name the category by its complete path."""
        for rec in self:
            if rec.parent_id:
                rec.display_name = f"{rec.parent_id.display_name} / {rec.name}"
            else:
                rec.display_name = rec.name

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(
                _("You cannot create a recursive chain of categories.")
            )
