from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    env.cr.execute(
        """
    SELECT id FROM advocate_engagement
    WHERE name = 'Prayer'
    """
    )
    prayer_engagement = env.cr.fetchone()
    if prayer_engagement:
        prayer_engagement_id = prayer_engagement[0]
        openupgrade.add_xmlid(
            env.cr,
            "partner_compassion",
            "engagement_pray",
            "advocate.engagement",
            prayer_engagement_id,
        )
    env.cr.execute(
        """
                   SELECT id FROM res_partner_category
                   WHERE name = 'Prayer'
                   """
    )
    prayer_tag = env.cr.fetchone()
    if prayer_tag:
        prayer_tag_id = prayer_tag[0]
        openupgrade.add_xmlid(
            env.cr,
            "partner_compassion",
            "res_partner_category_prayer",
            "res.partner.category",
            prayer_tag_id,
        )
