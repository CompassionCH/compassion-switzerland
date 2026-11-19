from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestQueueJobFunction(TransactionCase):
    def test_letter_import_job_may_commit(self):
        function = self.env.ref(
            "sbc_switzerland.job_function_import_letters_run_analyze"
        )
        self.assertEqual(function.name, "<import.letters.history>.run_analyze")
        self.assertTrue(function.allow_commit)

    def test_job_config_allows_commit(self):
        config = self.env["queue.job.function"].job_config(
            "<import.letters.history>.run_analyze"
        )
        self.assertTrue(config.allow_commit)
