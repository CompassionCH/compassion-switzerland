# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class QualityTest(models.Model):
    _name = "quality.test"
    _description = "Quality Test"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "category_id,sequence"
    _sql_constraints = [
        (
            "quality_test_sequence_uniq",
            "unique(sequence)",
            "The test number must be unique.",
        )
    ]

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Char(
        index=True,
        readonly=True,
        copy=False,
        default=lambda self: self.env["ir.sequence"].next_by_code("QTSEQ"),
        required=True,
    )
    test_version = fields.Char(
        tracking=True,
        readonly=True,
        default="1.0",
        required=True,
    )
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
    step_ids = fields.One2many(
        "quality.test.step",
        "test_id",
        string="Test Steps",
        domain=[("version_id", "=", False)],
        copy=True,
        help="Steps to perform, with the results expected for each of them.",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        domain=[("share", "=", False)],
    )
    parent_id = fields.Many2one(
        "quality.test",
        string="Parent",
        index=True,
        ondelete="set null",
        tracking=True,
        help="Test that must be performed before this one, when several tests "
        "are chained from a business perspective "
        "(e.g. 'Hold children' before 'Sponsor a child').",
    )
    child_ids = fields.One2many(
        "quality.test",
        "parent_id",
        string="Follow-up Tests",
        help="Tests that must be performed after this one.",
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
    last_notification = fields.Datetime()

    @api.depends("name", "test_version")
    def _compute_display_name(self):
        for rec in self:
            name = rec.name or ""
            display = f"{rec.sequence} - {name}".strip()
            rec.display_name = display if display else _("New Quality Test")

    @api.depends("test_run_ids")
    def _compute_run_count(self):
        for rec in self:
            rec.run_count = len(rec.test_run_ids)

    @api.depends("test_run_ids", "test_run_ids.date")
    def _compute_last_run(self):
        for rec in self:
            runs = rec.test_run_ids.sorted("date", reverse=True)
            rec.last_run_id = runs[:1]

    @api.constrains("parent_id")
    def _check_parent_id(self):
        if self._has_cycle():
            raise ValidationError(
                _("You cannot create a recursive chain of quality tests.")
            )

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
        return {
            "type": "ir.actions.act_window",
            "name": _("New Test Run"),
            "res_model": "quality.test.run",
            "view_mode": "form",
            "target": "current",
            "context": {
                "default_test_id": self.id,
                "default_result_ids": self._get_run_result_commands(),
                "default_module_version_ids": [
                    Command.create(
                        {
                            "module_id": module.id,
                            "version": module.installed_version,
                        }
                    )
                    for module in self.module_ids
                ],
            },
        }

    def action_view_runs(self):
        """Open the list of test runs for this quality test."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Test Runs"),
            "res_model": "quality.test.run",
            "view_mode": "list,form",
            "domain": [("test_id", "=", self.id)],
            "context": {"default_test_id": self.id},
        }

    def action_activate(self):
        """Move the test from draft to active, locking it for editing."""
        for rec in self:
            if rec.state == "draft":
                rec._check_steps_defined()
                rec.state = "active"
                version_exists = self.env["quality.test.version"].search_count(
                    [("test_id", "=", rec.id), ("version", "=", rec.test_version)]
                )
                if rec.run_count and version_exists:
                    rec.test_version = str(
                        float_round(float(rec.test_version) + 0.1, 1)
                    )
                version = self.env["quality.test.version"].create(
                    {
                        "version": rec.test_version,
                        "test_id": rec.id,
                    }
                )
                rec.step_ids.copy({"version_id": version.id})

    def _check_steps_defined(self):
        """Ensure the procedure is complete enough to be executed."""
        self.ensure_one()
        if not self.step_ids:
            raise UserError(
                _("Please define at least one test step before activating '%s'.")
                % self.display_name
            )
        incomplete_steps = self.step_ids.filtered(
            lambda step: not step.expected_result_ids
        )
        if incomplete_steps:
            raise UserError(
                _("The following steps have no expected result: %s")
                % ", ".join(incomplete_steps.mapped("name"))
            )

    def _get_version_record(self, version=None):
        """Return the version record holding the procedure of a given version."""
        self.ensure_one()
        return self.env["quality.test.version"].search(
            [
                ("test_id", "=", self.id),
                ("version", "=", version or self.test_version),
            ],
            limit=1,
        )

    def _get_run_result_commands(self, version=None):
        """Build the result lines to fill in during a run of the given version."""
        self.ensure_one()
        commands = []
        version_record = self._get_version_record(version)
        for step in version_record.step_ids:
            for expected in step.expected_result_ids:
                commands.append(
                    Command.create(
                        {
                            "step_id": step.id,
                            "expected_result_id": expected.id,
                            "sequence": len(commands),
                            "step_name": step.name,
                            "step_description": step.description,
                            "name": expected.name,
                        }
                    )
                )
        return commands

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
                # Delete versions that have no recorded runs
                runs = self.env["quality.test.run"].search_count(
                    [
                        ("test_id", "=", rec.id),
                        ("tested_at_version", "=", rec.test_version),
                    ]
                )
                if not runs:
                    self.env["quality.test.version"].search(
                        [("test_id", "=", rec.id), ("version", "=", rec.test_version)]
                    ).unlink()

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
            try:
                test._evaluate_rules()
            except Exception:
                _logger.exception(
                    "Quality test notification check failed for test %s (%s)",
                    test.id,
                    test.display_name,
                )

    def _evaluate_rules(self):
        """Evaluate notification rules for a single quality test and send
        an email to the responsible if a new run is needed."""
        self.ensure_one()
        reasons = []

        if self.rule_delay and self.delay_days > 0:
            threshold = fields.Datetime.now() - timedelta(days=self.delay_days)
            notification_due = (
                not self.last_notification or self.last_notification < threshold
            )
            if not self.last_run_date:
                if notification_due:
                    reasons.append(_("No test run has ever been recorded."))
            else:
                if self.last_run_date < threshold and notification_due:
                    days_ago = (fields.Datetime.now() - self.last_run_date).days
                    reasons.append(
                        _(
                            "Last run was %(days_ago)s day(s) ago "
                            "(max allowed: %(max_days)s days)."
                        )
                        % {"days_ago": days_ago, "max_days": self.delay_days}
                    )

        if self.rule_module_update and self.last_run_id:
            if self.last_run_id.instance == "stage":
                pass  # Stage runs may have newer versions; rule does not apply.
            else:
                outdated = self._get_outdated_modules()
                if outdated:
                    module_names = ", ".join(outdated.mapped("name"))
                    reasons.append(
                        _(
                            "The following modules have been updated since the last "
                            "test run: %s."
                        )
                        % module_names
                    )

        if reasons:
            self._send_notification_email(reasons)

    def _get_outdated_modules(self):
        """Return modules whose installed version differs from the version
        recorded in the last test run."""
        self.ensure_one()
        outdated = self.env["ir.module.module"].browse()
        last_run = self.last_run_id
        notification_due = (
            not self.last_notification
            or (fields.Datetime.now() - self.last_notification).days > 7
        )
        for version_rec in last_run.module_version_ids:
            module = version_rec.module_id
            current_version = module.installed_version or ""
            if (
                current_version
                and current_version != version_rec.version
                and notification_due
            ):
                outdated |= module
        return outdated

    def _send_notification_email(self, reasons):
        """Send an email notification to the responsible user."""
        self.ensure_one()
        template = self.env.ref(
            "quality_test_compassion.email_template_quality_test_notification",
            raise_if_not_found=False,
        )
        if template:
            template.with_context(notification_reasons=reasons).send_mail(
                self.id, force_send=True
            )
            self.last_notification = fields.Datetime.now()
