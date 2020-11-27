

def migrate(cr, version):
    if not version:
        return

    # Migrate crowdfunding participants to restrict on crowdfunding website
    cr.execute("""
        UPDATE crowdfunding_participant participant
        SET website_id = project.website_id,
            is_published = project.is_published
        FROM crowdfunding_project project
        WHERE participant.project_id = project.id
    """)
