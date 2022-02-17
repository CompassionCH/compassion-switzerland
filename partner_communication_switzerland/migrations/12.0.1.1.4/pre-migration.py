

def migrate(cr, installed_version):
    if not installed_version:
        return

    # Unlink removed communications rules to avoid database deletion.
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE name IN ('sponsorship_dossier_wrpr', 'email_wrpr_dossier')
        AND module = 'partner_communication_switzerland';
        UPDATE partner_communication_config
        SET active=false
        WHERE id=99;
    """)
