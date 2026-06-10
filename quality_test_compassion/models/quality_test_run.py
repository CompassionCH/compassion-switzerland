# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class QualityTestRun(models.Model):
    _name = "quality.test.run"
    _description = "Quality Test Run"
    _order = "date desc"
    _inherit = ["mail.thread"]

    test_id = fields.Many2one(
        "quality.test",
        string="Quality Test",
        required=True,
        ondelete="cascade",
        index=True,
    )
    date = fields.Datetime(
        string="Date",
        default=fields.Datetime.now,
        required=True,
        readonly=True,
    )
    result = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")],
        string="Result",
        required=True,
        tracking=True,
    )
    comment = fields.Text(string="Notes")
    task_id = fields.Many2one(
        "project.task",
        string="Fix Task",
        ondelete="set null",
        readonly=True,
        help="Project task created to track the resolution of a failing test.",
    )
    module_version_ids = fields.One2many(
        "quality.test.module.version",
        "run_id",
        string="Module Versions",
        readonly=True,
    )

    # Computed fields for convenience
    test_responsible_id = fields.Many2one(
        "res.users",
        string="Responsible",
        related="test_id.responsible_id",
        store=True,
    )
    test_department_id = fields.Many2one(
        "hr.department",
        string="Department",
        related="test_id.department_id",
        store=True,
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.result == "fail":
                record._send_fail_notification()
        return records

    def _send_fail_notification(self):
        """Send an email to the responsible when a failing test run is recorded."""
        self.ensure_one()
        responsible = self.test_id.responsible_id
        if not responsible or not responsible.email:
            return
        template = self.env.ref(
            "quality_test_compassion.email_template_quality_test_run_fail",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def action_create_task(self):
        """Create a project.task to track the resolution of a failing test."""
        self.ensure_one()
        if self.result != "fail":
            return
        if self.task_id:
            return self._open_task()

        task = self.env["project.task"].create(
            {
                "name": _("Fix failing quality test: %s", self.test_id.name),
                "description": _(
                    "A test run recorded on %(date)s has failed.\n\nNotes:\n%(comment)s",
                    date=self.date,
                    comment=self.comment or "",
                ),
                "user_ids": self.test_id.responsible_id
                and [(4, self.test_id.responsible_id.id)]
                or [],
            }
        )
        self.task_id = task
        return self._open_task()

    def _open_task(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Fix Task"),
            "res_model": "project.task",
            "res_id": self.task_id.id,
            "view_mode": "form",
            "target": "current",
        }
