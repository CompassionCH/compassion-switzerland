# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


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
    result = fields.Selection([("pass", "Pass"), ("fail", "Fail")])
    comment = fields.Text(string="Notes")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._notify_failed_runs()
        return records

    def write(self, vals):
        result = super().write(vals)
        if "result" in vals:
            self._notify_failed_runs()
        return result

    def _notify_failed_runs(self):
        """Warn the responsible when checking an expected result makes a run fail."""
        checked = self.filtered("result")
        checked.run_step_id.run_id._send_fail_notification()
