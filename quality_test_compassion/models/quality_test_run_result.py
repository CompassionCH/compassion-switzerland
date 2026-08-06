# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class QualityTestRunResult(models.Model):
    """Outcome of one expected result during a test run.

    The step and expected result texts are copied on the line so that the
    history of a run stays readable even if the test procedure changes
    afterwards.
    """

    _name = "quality.test.run.result"
    _description = "Quality Test Run Result"
    _order = "sequence,id"

    run_id = fields.Many2one(
        "quality.test.run",
        string="Test Run",
        required=True,
        ondelete="cascade",
        index=True,
    )
    step_id = fields.Many2one(
        "quality.test.step",
        string="Step",
        ondelete="set null",
        readonly=True,
    )
    expected_result_id = fields.Many2one(
        "quality.test.expected.result",
        string="Expected Result",
        ondelete="set null",
        readonly=True,
    )
    sequence = fields.Integer(readonly=True)
    step_name = fields.Char(string="Step", required=True, readonly=True)
    step_description = fields.Html(string="Instructions", readonly=True)
    name = fields.Char(string="Expected Result", required=True, readonly=True)
    result = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")],
        string="Result",
    )
    comment = fields.Text(string="Notes")
