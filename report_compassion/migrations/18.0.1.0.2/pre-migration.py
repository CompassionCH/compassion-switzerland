from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """The 'report_compassion_qr_slip' view (report/bvr_layout.xml) was
    reworked for v18 (dropped the removed l10n_ch_iban _is_qr_iban()
    method in favor of bank_account.l10n_ch_qr_iban), but its
    ir_model_data got noupdate=True at some point (most likely an
    in-place edit via the view editor), so the ordinary module upgrade
    below never reloads it and it keeps crashing on the old v14 content.
    Clear the flag first so the data file reload picks up the fix.
    """
    env.cr.execute(
        """
        UPDATE ir_model_data
        SET noupdate = false
        WHERE module = 'report_compassion'
          AND name = 'report_compassion_qr_slip'
          AND model = 'ir.ui.view'
        """
    )
