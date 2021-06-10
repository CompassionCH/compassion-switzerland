

def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        INSERT INTO mass_mailing_contact_partner_rel
        SELECT partner_id, id AS mass_mailing_contact_id
        FROM mail_mass_mailing_contact
        WHERE partner_id IS NOT NULL;
    """)

    # Attach other existing partners with same email
    cr.execute("""
        INSERT INTO mass_mailing_contact_partner_rel
        SELECT p.id AS partner_id, m.id AS mass_mailing_contact_id
        FROM res_partner p JOIN mail_mass_mailing_contact m
            ON p.email = m.email AND p.id != m.partner_id
        WHERE p.contact_type = 'standalone'
        AND p.email IS NOT NULL
    """)
