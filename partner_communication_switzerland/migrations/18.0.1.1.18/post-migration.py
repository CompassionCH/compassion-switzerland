import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# T3707: the Italian text of the "Donation - Christmas" thank-you letter was
# written for invoices. Since fund QR payments are booked on the bank line
# (no invoice, T3622):
# - it read the invoice date, empty on a bank move: the text could not be written
#   and no letter was created. The accounting date works for both;
# - it added up price_subtotal for the amount, which is negative or empty on a
#   bank line ("-50 CHF", "0 CHF"). get_donation_amount() (thankyou_letters) gives
#   the donated amount for invoices and bank lines alike.
# The template only lives in the database: it is matched by id and name, and only
# the Italian text still holding a faulty expression is changed. The stored text
# escapes quotes, both spellings are accepted.
TEMPLATE_ID = 197
TEMPLATE_NAME = "Donation - Christmas"
LANG = "it_IT"
DONATION_AMOUNT = "invoice_lines.get_donation_amount()"
FIXES = [
    ("invoices[0].invoice_date.month", "invoices[0].date.month"),
    ("sum(invoice_lines.mapped(&#x27;price_subtotal&#x27;))", DONATION_AMOUNT),
    ("sum(invoice_lines.mapped('price_subtotal'))", DONATION_AMOUNT),
]


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
    body = row and row[0]
    if not body:
        _logger.info(
            "T3707: mail.template %s %s (%s) not found",
            TEMPLATE_ID,
            TEMPLATE_NAME,
            LANG,
        )
        return
    changed = False
    for old, new in FIXES:
        count = body.count(old)
        if not count:
            continue
        body = body.replace(old, new)
        changed = True
        _logger.info(
            "T3707: mail.template %s %s (%s): %s replaced by %s (%s time(s))",
            TEMPLATE_ID,
            TEMPLATE_NAME,
            LANG,
            old,
            new,
            count,
        )
    if not changed:
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
        ([LANG], body, TEMPLATE_ID),
    )
    env["mail.template"].invalidate_model(["body_html"])
