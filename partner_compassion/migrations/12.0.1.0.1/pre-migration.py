def migrate(cr, version):
    if not version:
        return

    # Update employee field to be correct
    cr.execute("""
        UPDATE res_partner
        SET employee = not res_users.share
        FROM res_users
        WHERE res_partner.id = res_users.partner_id;
    """)
