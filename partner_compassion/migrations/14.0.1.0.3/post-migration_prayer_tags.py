from openupgradelib import openupgrade

from odoo import fields


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return

    partner = env["res.partner"]
    advocate_details = env["advocate.details"]
    advocate_engagement = env["advocate.engagement"]

    # Find the "Prayer" category (tag)
    prayer_tag = env["res.partner.category"].search([("name", "=", "Prayer")], limit=1)
    if not prayer_tag:
        return  # nothing to do if tag does not exist

    # Find or create the "Prayer" engagement type
    prayer_engagement = advocate_engagement.search([("name", "=", "Prayer")], limit=1)
    if not prayer_engagement:
        prayer_engagement = advocate_engagement.create({"name": "Prayer"})

    # All partners with the tag "Prayer"
    partners = partner.search([("category_id", "in", prayer_tag.ids)])

    for part in partners:
        # Ensure advocate.details exists
        advocate = part.advocate_details_id
        if not advocate:
            advocate = advocate_details.search([("partner_id", "=", part.id)])
            if not advocate:
                advocate = advocate_details.create(
                    {
                        "partner_id": part.id,
                        "active_since": fields.Date.today(),  # <-- set today's date
                    }
                )
            part.advocate_details_id = advocate.id

        # Add engagement if not already there
        if prayer_engagement not in advocate.engagement_ids:
            advocate.engagement_ids = [(4, prayer_engagement.id)]

    # Update the tag Prayer to be a smart tag
    prayer_tag.write(
        {
            "smart": True,
            "tag_filter_sql_query": """
            SELECT p.id
            FROM res_partner p
            JOIN advocate_details ad ON ad.partner_id = p.id
            JOIN advocate_engagement_rel rel ON rel.advocate_details_id = ad.id
            JOIN advocate_engagement eng ON eng.id = rel.engagement_id
            WHERE eng.name = 'Prayer'
        """,
        }
    )
