# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


def reduce_results(results):
    """Compute the overall outcome of a quality test based on the results of
    its steps result.

    False is returned if any result is also set to False.
    """
    if not results or not all(results):
        return False
    return "fail" if "fail" in results else "pass"


class QualityTestRunResult(models.Model):
    """Outcome of one expected result during a test run.

    The expected result text is copied on the line so that the history of a run
    stays readable even if the test procedure changes afterwards.
    """

    _name = "quality.test.run.result"
    _description = "Quality Test Run Result"
    _order = "sequence,id"

    run_step_id = fields.Many2one(
        "quality.test.run.step",
        string="Step",
        required=True,
        ondelete="cascade",
        index=True,
    )
    expected_result_id = fields.Many2one(
        "quality.test.expected.result",
        string="Expected Result",
        ondelete="set null",
        readonly=True,
    )
    sequence = fields.Integer(readonly=True)
    step_name = fields.Char(related="run_step_id.name", string="Step")
    name = fields.Char(string="Expected Result", required=True, readonly=True)
    result = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")],
        string="Result",
    )
    comment = fields.Text(string="Notes")
