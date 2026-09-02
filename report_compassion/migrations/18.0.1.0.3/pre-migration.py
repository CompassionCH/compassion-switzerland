from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """The 'tax_receipt' view (report/tax_receipt.xml) was reworked to use
    'object' + the 'tax_receipt_content' sub-template instead of a 'texts'
    dict passed in the report data, but its ir_model_data got noupdate=True
    at some point (most likely an in-place edit via the view editor), so the
    ordinary module upgrade below never reloads it. It keeps crashing with
    "TypeError: 'NoneType' object is not subscriptable" (texts[partner.id]
    where 'texts' is never set) on every tax receipt download. Same failure
    mode as 'report_compassion_qr_slip' in 18.0.1.0.2 - clear the flag first
    so the data file reload picks up the fix.
    """
    env.cr.execute(
        """
        UPDATE ir_model_data
        SET noupdate = false
        WHERE module = 'report_compassion'
          AND name = 'tax_receipt'
          AND model = 'ir.ui.view'
        """
    )
