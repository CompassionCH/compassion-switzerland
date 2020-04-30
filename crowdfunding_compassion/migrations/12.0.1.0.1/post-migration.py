def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        SELECT partner.id AS partner_id, project.id AS project_id
        FROM crowdfunding_project project JOIN crowdfunding_participant participant
        ON project.project_owner_id = participant.id
        JOIN res_partner partner ON participant.partner_id = partner.id
    """)
    for row in cr.fetchall():
        cr.execute("""
            UPDATE crowdfunding_project
            SET project_owner_id = %s
            WHERE id = %s
        """, row)
    cr.execute(
        "UPDATE crowdfunding_project SET state = 'draft' WHERE state = 'validation'")
