"""
auth_external — keep password hashes out of the server log.

When a query fails (serialization failure, lock timeout, deadlock), Odoo
core logs the full query with its parameters as "bad query". The password
rehash done at login (`_set_encrypted_password`) is such a query, so the
new hash ends up in odoo.log. The error cannot be caught before it is
logged, hence a filter on the odoo.sql_db logger.
"""

import logging
import re

# Matches password='...' as written in a raw query or in its bytes repr,
# where the quotes are escaped (password=\'...\').
PASSWORD_RE = re.compile(r"(password\s*=\s*)\\?'[^']*'", re.IGNORECASE)
REDACTED = "'********'"


class RedactPasswordFilter(logging.Filter):
    def filter(self, record):
        message = record.getMessage()
        redacted = PASSWORD_RE.sub(lambda m: m.group(1) + REDACTED, message)
        if redacted != message:
            record.msg = redacted
            record.args = None
        return True


def post_load():
    logger = logging.getLogger("odoo.sql_db")
    if not any(isinstance(f, RedactPasswordFilter) for f in logger.filters):
        logger.addFilter(RedactPasswordFilter())
