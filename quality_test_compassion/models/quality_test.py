# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class QualityTest(models.Model):
    _name = "quality.test"
    _description = "Quality Test"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(string="Name", required=True, tracking=True)
    category_id = fields.Many2one(
        "quality.test.category",
        string="Category",
        tracking=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("retired", "Retired"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        help="Draft: test is being prepared and can be freely edited.\n"
        "Active: test is locked for editing; test runs can be recorded.\n"
        "Retired: test is no longer relevant and cannot receive new runs.",
    )
    description = fields.Html(string="Description")
    responsible_id = fields.Many2one(
        "res.users",
        string="Responsible",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        tracking=True,
    )
    module_ids = fields.Many2many(
        "ir.module.module",
        "quality_test_module_rel",
        "test_id",
        "module_id",
        string="Related Modules",
        domain=[("state", "=", "installed")],
        help="Installed modules that affect the outcome of this test.",
    )
    test_run_ids = fields.One2many(
        "quality.test.run",
        "test_id",
        string="Test Runs",
        readonly=True,
    )
    run_count = fields.Integer(
        string="# Runs",
        compute="_compute_run_count",
        store=True,
    )
    last_run_id = fields.Many2one(
        "quality.test.run",
        string="Last Run",
        compute="_compute_last_run",
        store=True,
    )
    last_run_date = fields.Datetime(
        string="Last Run Date",
        related="last_run_id.date",
        store=True,
    )
    last_run_result = fields.Selection(
        string="Last Result",
        related="last_run_id.result",
        store=True,
    )

    # Notification rules
    rule_delay = fields.Boolean(
        string="Notify After Delay",
        help="Send an email to the responsible if no test run has occurred "
        "within the specified number of days.",
    )
    delay_days = fields.Integer(
        string="Max Days Between Runs",
        default=30,
        help="Number of days allowed between test runs before a notification "
        "is sent.",
    )
    rule_module_update = fields.Boolean(
        string="Notify on Module Update",
        help="Send an email to the responsible when one of the related modules "
        "has been updated since the last test run.",
    )

    @api.depends("test_run_ids")
    def _compute_run_count(self):
        for rec in self:
            rec.run_count = len(rec.test_run_ids)

    @api.depends("test_run_ids", "test_run_ids.date")
    def _compute_last_run(self):
        for rec in self:
            runs = rec.test_run_ids.sorted("date", reverse=True)
            rec.last_run_id = runs[:1]

    def action_create_run(self):
        """Open a new test run form pre-linked to this quality test."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(
                _(
                    "Test runs can only be recorded for active quality tests. "
                    "Please activate the test first."
                )
            )
        run = self.env["quality.test.run"].create(
            {
                "test_id": self.id,
                "module_version_ids": [
                    (
                        0,
                        0,
                        {
                            "module_id": module.id,
                            "version": module.installed_version or "",
                        },
                    )
                    for module in self.module_ids
                ],
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("New Test Run"),
            "res_model": "quality.test.run",
            "res_id": run.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_runs(self):
        """Open the list of test runs for this quality test."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Test Runs"),
            "res_model": "quality.test.run",
            "view_mode": "tree,form",
            "domain": [("test_id", "=", self.id)],
            "context": {"default_test_id": self.id},
        }

    def action_activate(self):
        """Move the test from draft to active, locking it for editing."""
        for rec in self:
            if rec.state == "draft":
                rec.state = "active"

    def action_retire(self):
        """Mark the test as retired – it will no longer accept new runs."""
        for rec in self:
            if rec.state in ("draft", "active"):
                rec.state = "retired"

    def action_reset_to_draft(self):
        """Return a retired or active test to draft for rework."""
        for rec in self:
            if rec.state in ("active", "retired"):
                rec.state = "draft"

    def check_rules_and_notify(self):
        """Check all quality tests against their notification rules and send
        emails to responsible users when a new test run is required."""
        tests = self.search(
            [
                ("state", "=", "active"),
                "|",
                ("rule_delay", "=", True),
                ("rule_module_update", "=", True),
            ]
        )
        for test in tests:
            test._evaluate_rules()

    def _evaluate_rules(self):
        """Evaluate notification rules for a single quality test and send
        an email to the responsible if a new run is needed."""
        self.ensure_one()
        reasons = []

        if self.rule_delay and self.delay_days > 0:
            if not self.last_run_date:
                reasons.append(_("No test run has ever been recorded."))
            else:
                threshold = fields.Datetime.now() - timedelta(days=self.delay_days)
                if self.last_run_date < threshold:
                    days_ago = (
                        fields.Datetime.now() - self.last_run_date
                    ).days
                    reasons.append(
                        _(
                            "Last run was %d day(s) ago (max allowed: %d days).",
                            days_ago,
                            self.delay_days,
                        )
                    )

        if self.rule_module_update and self.last_run_id:
            outdated = self._get_outdated_modules()
            if outdated:
                module_names = ", ".join(outdated.mapped("name"))
                reasons.append(
                    _(
                        "The following modules have been updated since the last "
                        "test run: %s.",
                        module_names,
                    )
                )

        if reasons:
            self._send_notification_email(reasons)

    def _get_outdated_modules(self):
        """Return modules whose installed version differs from the version
        recorded in the last test run."""
        self.ensure_one()
        outdated = self.env["ir.module.module"].browse()
        last_run = self.last_run_id
        for version_rec in last_run.module_version_ids:
            current_version = version_rec.module_id.installed_version or ""
            if current_version and current_version != version_rec.version:
                outdated |= version_rec.module_id
        return outdated

    def _send_notification_email(self, reasons):
        """Send an email notification to the responsible user."""
        self.ensure_one()
        template = self.env.ref(
            "quality_test_compassion.email_template_quality_test_notification",
            raise_if_not_found=False,
        )
        if not template:
            raise UserError(
                _("Email template for quality test notification not found.")
            )
        template.with_context(notification_reasons=reasons).send_mail(
            self.id, force_send=True
        )
