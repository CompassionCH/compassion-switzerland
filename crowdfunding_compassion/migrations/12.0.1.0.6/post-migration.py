

def migrate(cr, version):
    if not version:
        return

    # Migrate crowdfunding events to avoid spanning in calendar
    cr.execute("""
        UPDATE crm_event_compassion
        SET start_date = end_date
        WHERE crowdfunding_project_id IS NOT NULL;
    """)
