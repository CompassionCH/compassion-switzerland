from openupgradelib import openupgrade


def migrate(cr, installed_version):
    if not installed_version:
        return

    # Update is_first_sponsorship
    cr.execute("""
    UPDATE recurring_contract c
    SET is_first_sponsorship = true
    FROM res_partner p
    WHERE p.id = correspondent_id
    AND p.number_sponsorships = 0
    AND c.state in ('waiting','mandate')
    AND c.child_id IS NOT NULL;
    """)

    # Update data
    openupgrade.load_xml(
        cr, "partner_communication_switzerland", "data/onboarding_process.xml")

    # Update New Dossier communication
    cr.execute("""
    UPDATE partner_communication_config
    SET attachments_function = 'get_print_dossier_attachments'
    WHERE id IN (19,99,192);
    """)
