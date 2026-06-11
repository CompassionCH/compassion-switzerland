# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProjectTask(models.Model):
    _inherit = "project.task"

    quality_test_run_id = fields.Many2one(
        "quality.test.run",
        string="Failing Test Run",
        ondelete="set null",
    )

    def _sync_quality_test_run_links(self):
        for task in self:
            linked_run = task.quality_test_run_id
            if linked_run and linked_run.task_id != task:
                linked_run.task_id = task

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        tasks._sync_quality_test_run_links()
        return tasks

    def write(self, vals):
        previous_runs = self.mapped("quality_test_run_id")
        result = super().write(vals)
        self._sync_quality_test_run_links()
        if "quality_test_run_id" in vals:
            (previous_runs - self.mapped("quality_test_run_id")).filtered(
                lambda run: run.task_id in self
            ).write({"task_id": False})
        return result
