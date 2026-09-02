# Copyright 2026 Compassion CH
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from collections import defaultdict
from datetime import timedelta

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_round

_logger = logging.getLogger(__name__)


class QualityTest(models.Model):
    _name = "quality.test"
    _description = "Quality Test"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "category_id,sequence"

    name = fields.Char(required=True, tracking=True)
    sequence = fields.Char(
        index=True,
        readonly=True,
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
    description = fields.Html(required=True)
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        domain=[("share", "=", False)],
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

    @api.model
    def _build_dashboard_card(
        self, key, step_label, title, count, total, domain, color, deltas
    ):
        percentage = (count / total * 100) if total else 0.0
        return {
            "action_name": title,
            "color": color,
            "count": count,
            "deltas": deltas,
            "domain": domain,
            "key": key,
            "percentage": percentage,
            "status": self._get_dashboard_status(key, count, total),
            "step_label": step_label,
            "title": title,
        }

    @api.model
    def _get_dashboard_status(self, key, count, total):
        remaining = max(total - count, 0)
        status_by_key = {
            "draft": _("Still in draft: %s") % remaining,
            "executed": _("Without any test run yet: %s") % remaining,
            "passed": _("Not passing yet: %s") % remaining,
        }
        return status_by_key[key]

    @api.model
    def _get_state_label_map(self):
        languages = {self.env.lang, "en_US", "fr_CH", "fr_FR"}
        mapping = {
            value.casefold(): value
            for value, _label in self._fields["state"].selection
        }
        for lang in filter(None, languages):
            field_data = self.with_context(lang=lang).fields_get(["state"])["state"]
            for value, label in field_data["selection"]:
                mapping[label.casefold()] = value
                mapping[value.casefold()] = value
        return mapping

    @api.model
    def _get_state_by_test_at(self, reference_date):
        tests = self.search([("create_date", "<=", reference_date)])
        states = {test.id: test.state for test in tests}
        if not tests:
            return states
        label_map = self._get_state_label_map()
        self.env["mail.message"].flush_model(["model", "res_id", "date"])
        self.env["mail.tracking.value"].flush_model(
            ["field_id", "mail_message_id", "old_value_char", "new_value_char"]
        )
        self.env.cr.execute(
            """
            SELECT mm.res_id, mtv.old_value_char, mtv.new_value_char
            FROM mail_tracking_value mtv
            JOIN mail_message mm ON mm.id = mtv.mail_message_id
            JOIN ir_model_fields imf ON imf.id = mtv.field_id
            WHERE mm.model = %s
              AND mm.res_id = ANY(%s)
              AND imf.model = %s
              AND imf.name = 'state'
              AND mm.date > %s
            ORDER BY mm.res_id, mm.date DESC, mtv.id DESC
            """,
            [self._name, tests.ids, self._name, reference_date],
        )
        tracking_by_test = defaultdict(list)
        for res_id, old_value, new_value in self.env.cr.fetchall():
            tracking_by_test[res_id].append((old_value, new_value))
        for test in tests:
            state = test.state
            for old_value, new_value in tracking_by_test.get(test.id, []):
                old_state = label_map.get((old_value or "").casefold())
                new_state = label_map.get((new_value or "").casefold())
                if new_state == state and old_state:
                    state = old_state
            states[test.id] = state
        return states

    @api.model
    def _get_run_snapshot_at(self, reference_date, test_ids):
        if not test_ids:
            return set(), set()
        self.env["quality.test.run"].flush_model(["test_id", "date", "result"])
        self.env.cr.execute(
            """
            SELECT DISTINCT test_id
            FROM quality_test_run
            WHERE test_id = ANY(%s)
              AND date <= %s
            """,
            [test_ids, reference_date],
        )
        executed_ids = {row[0] for row in self.env.cr.fetchall()}
        self.env.cr.execute(
            """
            SELECT DISTINCT ON (test_id) test_id, result
            FROM quality_test_run
            WHERE test_id = ANY(%s)
              AND date <= %s
            ORDER BY test_id, date DESC, id DESC
            """,
            [test_ids, reference_date],
        )
        passed_ids = {
            test_id for test_id, result in self.env.cr.fetchall() if result == "pass"
        }
        return executed_ids, passed_ids

    @api.model
    def _get_dashboard_snapshot_at(self, reference_date):
        state_by_test = self._get_state_by_test_at(reference_date)
        active_test_ids = [
            test_id for test_id, state in state_by_test.items() if state != "retired"
        ]
        draft_count = sum(1 for state in state_by_test.values() if state == "draft")
        executed_ids, passed_ids = self._get_run_snapshot_at(
            reference_date, active_test_ids
        )
        return {
            "draft": draft_count,
            "executed": len(executed_ids),
            "passed": len(passed_ids),
            "total": len(active_test_ids),
        }

    @api.model
    def _get_dashboard_delta(self, current_snapshot, previous_snapshot, key):
        current_total = current_snapshot["total"]
        previous_total = previous_snapshot["total"]
        current_percentage = (
            current_snapshot[key] / current_total * 100 if current_total else 0.0
        )
        previous_percentage = (
            previous_snapshot[key] / previous_total * 100 if previous_total else 0.0
        )
        percentage_delta = round(current_percentage - previous_percentage, 1)
        count_delta = current_snapshot[key] - previous_snapshot[key]
        return {
            "count_delta": count_delta,
            "direction": (
                "positive"
                if percentage_delta > 0
                else "negative" if percentage_delta < 0 else "neutral"
            ),
            "label": _("%(points).1f pts (%(count)+d)")
            % {
                "count": count_delta,
                "points": percentage_delta,
            },
            "percentage_delta": percentage_delta,
        }

    @api.model
    def _get_dashboard_deltas(
        self, current_snapshot, week_snapshot, month_snapshot, key
    ):
        return [
            {
                "key": "week",
                "label": _("Since last week"),
                **self._get_dashboard_delta(current_snapshot, week_snapshot, key),
            },
            {
                "key": "month",
                "label": _("Since last month"),
                **self._get_dashboard_delta(current_snapshot, month_snapshot, key),
            },
        ]

    @api.model
    def get_dashboard_metrics(self):
        now = fields.Datetime.now()
        current_snapshot = self._get_dashboard_snapshot_at(now)
        week_snapshot = self._get_dashboard_snapshot_at(now - timedelta(days=7))
        month_snapshot = self._get_dashboard_snapshot_at(now - timedelta(days=30))
        total = current_snapshot["total"]
        cards = [
            self._build_dashboard_card(
                "draft",
                _("Step 1"),
                _("Tests to validate"),
                current_snapshot["draft"],
                total,
                [("state", "=", "draft")],
                "primary",
                self._get_dashboard_deltas(
                    current_snapshot, week_snapshot, month_snapshot, "draft"
                ),
            ),
            self._build_dashboard_card(
                "executed",
                _("Step 2"),
                _("Tests executed"),
                current_snapshot["executed"],
                total,
                [("state", "!=", "retired"), ("run_count", ">", 0)],
                "info",
                self._get_dashboard_deltas(
                    current_snapshot, week_snapshot, month_snapshot, "executed"
                ),
            ),
            self._build_dashboard_card(
                "passed",
                _("Step 3"),
                _("Tests passed"),
                current_snapshot["passed"],
                total,
                [("state", "!=", "retired"), ("last_run_result", "=", "pass")],
                "success",
                self._get_dashboard_deltas(
                    current_snapshot, week_snapshot, month_snapshot, "passed"
                ),
            ),
        ]
        return {
            "cards": cards,
            "generated_at": fields.Datetime.to_string(now),
            "subtitle": _("Refresh the page to update the figures."),
            "title": _("Quality tests dashboard"),
            "total": total,
        }

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
                rec.state = "active"
                version_exists = self.env["quality.test.version"].search_count(
                    [("test_id", "=", rec.id), ("version", "=", rec.test_version)]
                )
                if rec.run_count and version_exists:
                    rec.test_version = str(
                        float_round(float(rec.test_version) + 0.1, 1)
                    )
                self.env["quality.test.version"].create(
                    {
                        "version": rec.test_version,
                        "description": rec.description,
                        "test_id": rec.id,
                    }
                )

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
