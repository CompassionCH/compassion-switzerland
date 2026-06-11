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
    user_id = fields.Many2one(
        "res.users",
        string="Tester",
        required=True,
        default=lambda self: self.env.user,
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
    instance = fields.Selection(
        [("production", "Production"), ("stage", "Stage")],
        string="Instance",
        required=True,
        default="production",
        tracking=True,
        help="Instance on which the test was performed.\n"
        "Production: module versions are captured automatically.\n"
        "Stage: module versions are not auto-filled and can be set manually, "
        "as the stage may run a newer version than production.",
    )
    comment = fields.Html(string="Notes")
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

    @api.onchange("instance")
    def _onchange_instance(self):
        """Clear module versions when switching to stage; they must be set manually."""
        if self.instance == "stage":
            self.module_version_ids = [(5, 0, 0)]

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
        if self.task_id:
            return {
                "type": "ir.actions.act_window",
                "name": _("Fix Task"),
                "res_model": "project.task",
                "res_id": self.task_id.id,
                "view_mode": "form",
                "target": "current",
            }
        return {
            "type": "ir.actions.act_window",
            "name": _("Fix Task"),
            "res_model": "project.task",
            "res_id": self.task_id.id,
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_name": f"Fix failing quality test: {self.test_id.name}",
                "default_description": (
                    f"A test run recorded on {self.date} has failed.\n\n"
                    f"Notes:\n{self.comment or ''}"
                ),
                "default_quality_test_run_id": self.id,
                "default_user_id": self.test_id.responsible_id.id,
                "default_project_id": self.env["project.project"]
                .search([], limit=1)
                .id,
                "default_partner_id": self.env.user.partner_id.id,
            },
        }
