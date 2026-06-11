# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class QualityTestRun(models.Model):
    _name = "quality.test.run"
    _description = "Quality Test Run"
    _order = "date desc"
    _inherit = ["mail.thread"]
    _sql_constraints = [
        (
            "quality_test_run_test_sequence_uniq",
            "unique(test_id, sequence)",
            "The run sequence must be unique per quality test.",
        )
    ]

    test_id = fields.Many2one(
        "quality.test",
        string="Quality Test",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(
        string="Run #",
        required=True,
        readonly=True,
        copy=False,
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
        related="test_id.user_id",
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
        default_test_id = self.env.context.get("default_test_id")
        test_ids = set()
        for vals in vals_list:
            test_id = vals.get("test_id", default_test_id)
            if test_id:
                test_ids.add(test_id)

        sequence_by_test = {}
        if test_ids:
            # Lock parent tests to make sequence allocation atomic per test.
            self.env.cr.execute(
                """
                SELECT id
                FROM quality_test
                WHERE id = ANY(%s)
                ORDER BY id
                FOR UPDATE
                """,
                [sorted(test_ids)],
            )
            self.env.cr.execute(
                """
                SELECT test_id, COALESCE(MAX(sequence), 0)
                FROM quality_test_run
                WHERE test_id = ANY(%s)
                GROUP BY test_id
                """,
                [sorted(test_ids)],
            )
            sequence_by_test = dict(self.env.cr.fetchall())

        for vals in vals_list:
            test_id = vals.get("test_id", default_test_id)
            if test_id and not vals.get("sequence"):
                next_sequence = sequence_by_test.get(test_id, 0) + 1
                vals["sequence"] = next_sequence
                sequence_by_test[test_id] = next_sequence

        records = super().create(vals_list)
        for record in records:
            if record.result == "fail":
                record._send_fail_notification()
        return records

    @api.depends("test_id.name", "sequence")
    def _compute_display_name(self):
        for rec in self:
            if rec.test_id and rec.sequence:
                rec.display_name = f"{rec.test_id.name} - #{rec.sequence}"
            elif rec.test_id:
                rec.display_name = rec.test_id.name
            else:
                rec.display_name = _("New Test Run")

    def _send_fail_notification(self):
        """Send an email to the responsible when a failing test run is recorded."""
        self.ensure_one()
        responsible = self.test_responsible_id
        template = self.env.ref(
            "quality_test_compassion.email_template_quality_test_run_fail",
            raise_if_not_found=False,
        )
        if responsible != self.user_id and responsible.email and template:
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
                "default_user_id": self.test_id.user_id.id,
                "default_project_id": self.env["project.project"]
                .search([], order="sequence, id", limit=1)
                .id,
                "default_partner_id": self.env.user.partner_id.id,
            },
        }
