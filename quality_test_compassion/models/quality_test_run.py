# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from markupsafe import Markup

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
    test_version = fields.Char(related="test_id.test_version")
    tested_at_version = fields.Char("Protocol version", readonly=True)
    result_ids = fields.One2many(
        "quality.test.run.result",
        "run_id",
        string="Test Results",
        help="Expected results to check while performing the test.",
    )
    failed_result_ids = fields.Many2many(
        "quality.test.run.result",
        string="Failed Expected Results",
        compute="_compute_failed_result_ids",
    )
    failed_result_count = fields.Integer(compute="_compute_failed_result_ids")
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
        default=fields.Datetime.now,
        required=True,
        readonly=True,
    )
    result = fields.Selection(
        [("pass", "Pass"), ("fail", "Fail")],
        compute="_compute_result",
        store=True,
        tracking=True,
        help="Outcome of the run, derived from the expected results checked "
        "along the test procedure. It stays empty until all of them are "
        "checked.",
    )
    fail_notification_sent = fields.Boolean(
        readonly=True,
        copy=False,
        help="Technical field ensuring the responsible is warned only once "
        "that this run has failed.",
    )
    instance = fields.Selection(
        [("production", "Production"), ("stage", "Stage")],
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

    @api.depends("result_ids.result")
    def _compute_failed_result_ids(self):
        for rec in self:
            failed = rec.result_ids.filtered(lambda line: line.result == "fail")
            rec.failed_result_ids = failed
            rec.failed_result_count = len(failed)

    @api.depends("result_ids.result")
    def _compute_result(self):
        """Derive the overall result from the expected results of the procedure.

        The run has no result as long as an expected result is left unchecked.
        """
        for rec in self:
            results = rec.result_ids.mapped("result")
            if results and all(results):
                rec.result = "fail" if "fail" in results else "pass"
            else:
                rec.result = False

    @api.onchange("instance")
    def _onchange_instance(self):
        """Clear module versions when switching to stage; they must be set manually."""
        if self.instance == "stage":
            for module in self.module_version_ids:
                module.version = False
        elif self.instance == "production":
            for module in self.module_version_ids:
                module.version = module.module_id.installed_version

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

        tests = {test.id: test for test in self.env["quality.test"].browse(test_ids)}
        for vals in vals_list:
            test_id = vals.get("test_id", default_test_id)
            if not test_id:
                continue
            if not vals.get("sequence"):
                next_sequence = sequence_by_test.get(test_id, 0) + 1
                vals["sequence"] = next_sequence
                sequence_by_test[test_id] = next_sequence
            test = tests[test_id]
            # Freeze the procedure the run is about to follow.
            vals["tested_at_version"] = test.test_version
            if not vals.get("result_ids"):
                vals["result_ids"] = test._get_run_result_commands()

        records = super().create(vals_list)
        for record in records:
            if record.result == "fail":
                record._send_fail_notification()
        return records

    def write(self, vals):
        result = super().write(vals)
        for record in self.filtered(lambda run: run.result == "fail"):
            record._send_fail_notification()
        return result

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
        if self.fail_notification_sent:
            return
        responsible = self.test_responsible_id
        template = self.env.ref(
            "quality_test_compassion.email_template_quality_test_run_fail",
            raise_if_not_found=False,
        )
        if responsible != self.user_id and responsible.email and template:
            self.fail_notification_sent = True
            template.send_mail(self.id, force_send=True)

    def _get_failure_description(self):
        """Describe what went wrong during the run, for the fix task."""
        self.ensure_one()
        description = Markup("<p>%s</p>") % (
            _("Test run #%(run)s of %(test)s performed on %(date)s has failed.")
            % {
                "run": self.sequence,
                "test": self.test_id.display_name,
                "date": self.date,
            }
        )
        if self.failed_result_ids:
            failed_lines = Markup("")
            for line in self.failed_result_ids:
                failed_lines += Markup("<li><b>%(step)s</b>: %(expected)s%(notes)s</li>") % {
                    "step": line.step_name,
                    "expected": line.name,
                    "notes": Markup("<br/>%s") % line.comment if line.comment else "",
                }
            description += Markup("<p><b>%s</b></p><ul>%s</ul>") % (
                _("Failed expected results:"),
                failed_lines,
            )
        if self.comment:
            description += Markup("<p><b>%s</b></p>%s") % (_("Notes:"), self.comment)
        return description

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
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_name": _("Fix failing quality test: %s") % self.test_id.name,
                "default_description": self._get_failure_description(),
                "default_quality_test_run_id": self.id,
                "default_user_id": self.test_id.user_id.id,
                "default_project_id": self.env["project.project"]
                .search([], order="sequence, id", limit=1)
                .id,
                "default_partner_id": self.env.user.partner_id.id,
            },
        }
