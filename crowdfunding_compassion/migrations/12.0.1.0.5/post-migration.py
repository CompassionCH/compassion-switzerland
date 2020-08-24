

def migrate(cr, version):
    if not version:
        return

    # Migrate crowdfunding origins
    cr.execute("""
        UPDATE recurring_contract_origin
        SET type = 'crowdfunding'
        WHERE name ILIKE '%crowdfunding%'
    """)
