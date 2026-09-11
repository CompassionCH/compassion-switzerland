# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QualityTestStep(models.Model):
    _name = "quality.test.step"
    _description = "Quality Test Step"
    _order = "sequence,id"

    test_id = fields.Many2one(
        "quality.test",
        string="Quality Test",
        required=True,
        ondelete="cascade",
        index=True,
    )
    version_id = fields.Many2one(
        "quality.test.version",
        string="Test Version",
        ondelete="cascade",
        index=True,
        help="Frozen copy of the step, taken when the test version was "
        "activated. Steps without version are the ones currently edited.",
    )
    sequence = fields.Integer(default=10)
    name = fields.Char(string="Step", required=True)
    description = fields.Html(
        help="Detailed instructions to perform this step.",
    )
    expected_result_ids = fields.One2many(
        "quality.test.expected.result",
        "step_id",
        string="Expected Results",
        copy=True,
    )
