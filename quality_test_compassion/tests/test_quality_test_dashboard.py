from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestQualityTestDashboard(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls.env.ref("base.user_admin")

    def _create_test(self, name, state="draft"):
        return self.env["quality.test"].create(
            {
                "description": "<p>Test procedure</p>",
                "name": name,
                "state": state,
                "user_id": self.admin.id,
            }
        )

    def _set_record_dates(self, table, record_id, create_date=None, write_date=None):
        self.env.cr.execute(
            f"""
            UPDATE {table}
               SET create_date = COALESCE(%s, create_date),
                   write_date = COALESCE(%s, write_date)
             WHERE id = %s
            """,
            [create_date, write_date, record_id],
        )

    def _set_state_tracking_date(self, test, when):
        message = self.env["mail.message"].search(
            [
                ("model", "=", "quality.test"),
                ("res_id", "=", test.id),
                ("tracking_value_ids.field_id.name", "=", "state"),
            ],
            order="id desc",
            limit=1,
        )
        self._set_record_dates("mail_message", message.id, when, when)

    def test_dashboard_metrics_include_filters_and_deltas(self):
        now = fields.Datetime.now()
        old_date = now - timedelta(days=40)

        draft_test = self._create_test("Draft test")
        activated_this_week = self._create_test("Activated this week")
        active_with_pass = self._create_test("Active pass")
        active_with_fail = self._create_test("Active fail")

        for test in [
            draft_test,
            activated_this_week,
            active_with_pass,
            active_with_fail,
        ]:
            self._set_record_dates("quality_test", test.id, old_date, old_date)

        activated_this_week.action_activate()
        self._set_state_tracking_date(activated_this_week, now - timedelta(days=3))

        active_with_pass.action_activate()
        self._set_state_tracking_date(active_with_pass, now - timedelta(days=20))

        active_with_fail.action_activate()
        self._set_state_tracking_date(active_with_fail, now - timedelta(days=40))

        pass_run = self.env["quality.test.run"].create(
            {
                "date": now - timedelta(days=2),
                "instance": "production",
                "result": "pass",
                "test_id": active_with_pass.id,
                "user_id": self.admin.id,
            }
        )
        fail_run = self.env["quality.test.run"].create(
            {
                "date": now - timedelta(days=25),
                "instance": "production",
                "result": "fail",
                "test_id": active_with_fail.id,
                "user_id": self.admin.id,
            }
        )
        self._set_record_dates(
            "quality_test_run",
            pass_run.id,
            now - timedelta(days=2),
            now - timedelta(days=2),
        )
        self._set_record_dates(
            "quality_test_run",
            fail_run.id,
            now - timedelta(days=25),
            now - timedelta(days=25),
        )

        self.env.flush_all()
        metrics = self.env["quality.test"].get_dashboard_metrics()
        cards = {card["key"]: card for card in metrics["cards"]}

        self.assertEqual(metrics["title"], "Quality tests dashboard")
        self.assertEqual(metrics["total"], 4)
        self.assertEqual(cards["draft"]["count"], 1)
        self.assertEqual(cards["executed"]["count"], 2)
        self.assertEqual(cards["passed"]["count"], 1)
        self.assertEqual(cards["draft"]["domain"], [("state", "=", "draft")])
        self.assertEqual(
            cards["executed"]["domain"],
            [("state", "!=", "retired"), ("run_count", ">", 0)],
        )
        self.assertEqual(
            cards["passed"]["domain"],
            [("state", "!=", "retired"), ("last_run_result", "=", "pass")],
        )
        self.assertEqual(cards["draft"]["deltas"][0]["percentage_delta"], -25.0)
        self.assertEqual(cards["draft"]["deltas"][1]["percentage_delta"], -50.0)
        self.assertEqual(cards["executed"]["deltas"][0]["percentage_delta"], 25.0)
        self.assertEqual(cards["executed"]["deltas"][1]["percentage_delta"], 50.0)
        self.assertEqual(cards["passed"]["deltas"][0]["percentage_delta"], 25.0)
        self.assertEqual(cards["passed"]["deltas"][1]["percentage_delta"], 25.0)
