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

    def test_dashboard_metrics(self):
        self._create_test("Draft 1")
        self._create_test("Draft 2")
        active_with_pass = self._create_test("Active pass", state="active")
        active_with_fail = self._create_test("Active fail", state="active")
        self._create_test("Retired", state="retired")

        self.env["quality.test.run"].create(
            {
                "instance": "production",
                "result": "pass",
                "test_id": active_with_pass.id,
                "user_id": self.admin.id,
            }
        )
        self.env["quality.test.run"].create(
            {
                "instance": "production",
                "result": "fail",
                "test_id": active_with_fail.id,
                "user_id": self.admin.id,
            }
        )

        metrics = self.env["quality.test"].get_dashboard_metrics()
        cards = {card["key"]: card for card in metrics["cards"]}

        self.assertEqual(metrics["subtitle"], "Key metrics (3 validation stages)")
        self.assertEqual(metrics["total"], 4)
        self.assertEqual(cards["validated"]["count"], 2)
        self.assertEqual(cards["executed"]["count"], 2)
        self.assertEqual(cards["passed"]["count"], 1)
        self.assertEqual(cards["validated"]["domain"], [("state", "=", "draft")])
        self.assertEqual(cards["validated"]["click_domain"], [("state", "=", "draft")])
        self.assertEqual(
            cards["executed"]["domain"],
            [("state", "!=", "retired"), ("run_count", ">", 0)],
        )
        self.assertEqual(
            cards["executed"]["click_domain"],
            [("state", "!=", "retired"), ("run_count", "=", 0)],
        )
        self.assertEqual(
            cards["passed"]["domain"],
            [("state", "!=", "retired"), ("last_run_result", "=", "pass")],
        )
        self.assertEqual(
            cards["passed"]["click_domain"],
            [("state", "!=", "retired"), ("last_run_result", "=", "fail")],
        )
