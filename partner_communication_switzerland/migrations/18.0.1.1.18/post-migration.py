import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3707: the Italian text of the "Donation - Christmas" thank-you letter reads the
# invoice date. Since fund QR payments are booked on the bank line (no invoice),
# that date is empty, the text cannot be written and no letter is created.
# The accounting date works for invoices and bank lines alike.
# The template only lives in the database: it is matched by id and name, and only
# the Italian text still holding the faulty expression is changed.
TEMPLATE_ID = 197
TEMPLATE_NAME = "Donation - Christmas"
LANG = "it_IT"
OLD = "invoices[0].invoice_date.month"
NEW = "invoices[0].date.month"


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        """
        SELECT body_html->>%s FROM mail_template
        WHERE id = %s AND name->>'en_US' = %s
        """,
        (LANG, TEMPLATE_ID, TEMPLATE_NAME),
    )
    row = env.cr.fetchone()
    if not row or not row[0] or OLD not in row[0]:
        _logger.info(
            "T3707: mail.template %s %s (%s) has nothing to fix",
            TEMPLATE_ID,
            TEMPLATE_NAME,
            LANG,
        )
        return
    env.cr.execute(
        """
        UPDATE mail_template
        SET body_html = jsonb_set(body_html, %s, to_jsonb(%s::text))
        WHERE id = %s
        """,
        ([LANG], row[0].replace(OLD, NEW), TEMPLATE_ID),
    )
    env["mail.template"].invalidate_model(["body_html"])
    _logger.info(
        "T3707: mail.template %s %s (%s): %s replaced by %s (%s time(s))",
        TEMPLATE_ID,
        TEMPLATE_NAME,
        LANG,
        OLD,
        NEW,
        row[0].count(OLD),
    )
