

def migrate(cr, version):
    if not version:
        return

    # Migrate crowdfunding events to avoid spanning in calendar
    cr.execute("""
        UPDATE crowdfunding_project
        SET is_published = true
        WHERE state = 'active';
    """)
