# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QualityTestCategory(models.Model):
    _name = "quality.test.category"
    _description = "Quality Test Category"
    _order = "name"

    name = fields.Char(string="Name", required=True)
