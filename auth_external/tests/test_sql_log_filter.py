import logging

from odoo.tests.common import TransactionCase, tagged

from ..hooks import RedactPasswordFilter, post_load

HASH = "$pbkdf2-sha512$600000$abc.DEF$ghi/JKL"


@tagged("auth_external", "sql_log_filter")
class TestSqlLogFilter(TransactionCase):
    def _format(self, query):
        record = logging.LogRecord(
            "odoo.sql_db",
            logging.ERROR,
            __file__,
            1,
            "bad query: %s\nERROR: %s",
            (query, "could not serialize access"),
            None,
        )
        RedactPasswordFilter().filter(record)
        return record.getMessage()

    def test_hash_is_redacted_in_bytes_query(self):
        message = self._format(
            f"UPDATE res_users SET password='{HASH}' WHERE id=2".encode()
        )
        self.assertNotIn(HASH, message)
        self.assertIn("password='********'", message)

    def test_hash_is_redacted_in_escaped_repr(self):
        # A bytes query containing both quote types is repr'd with \' quotes
        message = self._format(
            f"UPDATE res_users SET name=\"x\", password='{HASH}'".encode()
        )
        self.assertNotIn(HASH, message)

    def test_other_queries_are_untouched(self):
        message = self._format("UPDATE res_partner SET name='x' WHERE id=2")
        self.assertIn("name='x'", message)

    def test_post_load_installs_filter_once(self):
        logger = logging.getLogger("odoo.sql_db")
        post_load()
        post_load()
        count = sum(isinstance(f, RedactPasswordFilter) for f in logger.filters)
        self.assertEqual(count, 1)
