# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QualityTestExpectedResult(models.Model):
    _name = "quality.test.expected.result"
    _description = "Quality Test Expected Result"
    _order = "sequence,id"

    step_id = fields.Many2one(
        "quality.test.step",
        string="Step",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(
        string="Expected Result",
        required=True,
        help="What must be observed for this step to be considered successful.",
    )
