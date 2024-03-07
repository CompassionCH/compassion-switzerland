from dateutil.relativedelta import relativedelta
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Associate already created toilets fund to new xml record
    sponsorships = env["recurring.contract"].search(
        [
            ("create_uid.name", "=", "WordPress Imports"),
            ("next_invoice_date", "!=", False),
            ("state", "not in", ["cancelled", "terminated"]),
        ]
    )

    for s in sponsorships:
        d = s.next_invoice_date
        if d.day != 1 and d.day != 25:
            month_delta = relativedelta(months=0 if d.day < 15 else 1)
            next_invoice = d.replace(day=1) + month_delta
            s.next_invoice_date = next_invoice
