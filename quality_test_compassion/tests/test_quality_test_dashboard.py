from odoo.tests.common import TransactionCase


class TestQualityTestDashboard(TransactionCase):
    def _create_test(self, name, state="draft"):
        return self.env["quality.test"].create(
            {
                "description": "<p>Test procedure</p>",
                "name": name,
                "state": state,
                "user_id": self.env.ref("base.user_admin").id,
            }
        )

    def test_dashboard_metrics_ignore_retired_tests(self):
        draft_test = self._create_test("Draft test")
        active_test = self._create_test("Active test", state="active")
        active_with_pass = self._create_test("Active pass", state="active")
        active_with_fail = self._create_test("Active fail", state="active")
        self._create_test("Retired test", state="retired")

        self.env["quality.test.run"].create(
            {
                "instance": "production",
                "result": "pass",
                "test_id": active_with_pass.id,
                "user_id": self.env.ref("base.user_admin").id,
            }
        )
        self.env["quality.test.run"].create(
            {
                "instance": "production",
                "result": "fail",
                "test_id": active_with_fail.id,
                "user_id": self.env.ref("base.user_admin").id,
            }
        )

        self.env.flush_all()
        metrics = self.env["quality.test"].get_dashboard_metrics()
        cards = {card["key"]: card for card in metrics["cards"]}

        self.assertEqual(metrics["total"], 4)
        self.assertEqual(cards["validated"]["count"], 3)
        self.assertEqual(cards["executed"]["count"], 2)
        self.assertEqual(cards["passed"]["count"], 1)
        self.assertEqual(
            cards["validated"]["domain"],
            [("state", "!=", "draft"), ("state", "!=", "retired")],
        )
        self.assertEqual(
            cards["executed"]["domain"],
            [("state", "!=", "retired"), ("run_count", ">", 0)],
        )
        self.assertEqual(
            cards["passed"]["domain"],
            [("state", "!=", "retired"), ("last_run_result", "=", "pass")],
        )
        self.assertEqual(draft_test.run_count, 0)
        self.assertEqual(active_test.run_count, 0)
