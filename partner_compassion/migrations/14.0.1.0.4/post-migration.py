from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    prayer_tag = env["res.partner.category"].search([("name", "=", "Prayer")])
    prayer_engagement = env.ref("partner_compassion.engagement_pray")
    prayer_tag.write(
        {
            "smart": True,
            "tag_filter_sql_query": """
            SELECT partner_id
            FROM advocate_engagement_rel rel
            JOIN advocate_details ad ON rel.advocate_details_id = ad.id
            WHERE rel.engagement_id = %s
        """
            % prayer_engagement.id,
        }
    )
    prayers = env["res.partner"].search([("category_id", "in", prayer_tag.id)])
    for prayer in prayers:
        prayer.engagement_ids += prayer_engagement
