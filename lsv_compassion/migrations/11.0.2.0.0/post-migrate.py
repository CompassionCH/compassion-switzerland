from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """Update database from previous versions, after updating module."""

    if not version:
        return

    # Correct charge_bearer for sepa bank_payment_line (must be 'SLEV')
    blines = env['bank.payment.line'].search([])
    for bline in blines:
        if bline.sepa:
            bline.charge_bearer = 'SLEV'
