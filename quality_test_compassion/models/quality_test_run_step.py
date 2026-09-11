# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from .quality_test_run_result import reduce_results


class QualityTestRunStep(models.Model):
    """One step to perform during a test run.

    The step texts are copied on the line so that the history of a run stays
    readable even if the test procedure changes afterwards.
    """

    _name = "quality.test.run.step"
    _description = "Quality Test Run Step"
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
    sequence = fields.Integer(readonly=True)
    name = fields.Char(string="Step", required=True, readonly=True)
    description = fields.Html(string="Instructions", readonly=True)
    result_ids = fields.One2many(
        "quality.test.run.result",
        "run_step_id",
        string="Expected Results",
        help="Expected results to check while performing this step.",
    )
    result = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")],
        compute="_compute_result",
        store=True,
        help="Outcome of the step, derived from its expected results. It stays "
        "empty until all of them are checked.",
    )
    checked_summary = fields.Char(
        string="Checked",
        compute="_compute_checked_summary",
        help="Number of expected results already checked for this step.",
    )

    @api.depends("result_ids.result")
    def _compute_result(self):
        for rec in self:
            rec.result = reduce_results(rec.result_ids.mapped("result"))

    @api.depends("result_ids.result")
    def _compute_checked_summary(self):
        for rec in self:
            checked = len(rec.result_ids.filtered("result"))
            rec.checked_summary = f"{checked} / {len(rec.result_ids)}"
