from openupgradelib import openupgrade


def migrate(cr, version):
    # Migrate OCA contacts to standard Odoo contacts
    if openupgrade.column_exists(cr, "res_partner", "contact_id"):
        openupgrade.logged_query(
            cr,
            """
            UPDATE res_partner
            SET parent_id = contact_id, active=true
            WHERE contact_id IS NOT NULL
        """,
        )
