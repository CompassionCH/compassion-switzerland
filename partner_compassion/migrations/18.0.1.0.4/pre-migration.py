import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# xmlid: English name of the engagement type created by hand in the database
ADOPTED_ENGAGEMENTS = {
    "engagement_church_advocate": "Church advocate",
    "engagement_office_volunteer": "Office volunteer",
}


@openupgrade.migrate()
def migrate(env, version):
    """These engagement types were created by hand in the database. They now
    ship with the module, for their export column on the advocates (T2740).
    Give the existing records the module's xmlids before the data loads, so
    that they are kept, with their advocates, instead of duplicates being
    created next to them. Models are not loaded yet in a pre-migration: SQL
    only.
    """
    for xmlid, name in ADOPTED_ENGAGEMENTS.items():
        env.cr.execute(
            """
            SELECT 1 FROM ir_model_data
            WHERE module = 'partner_compassion' AND name = %s
            """,
            (xmlid,),
        )
        if env.cr.fetchone():
            continue
        env.cr.execute(
            """
            SELECT id FROM advocate_engagement
            WHERE name->>'en_US' = %s
            ORDER BY id LIMIT 1
            """,
            (name,),
        )
        row = env.cr.fetchone()
        if not row:
            _logger.info("T2740: no %s engagement, the module creates it", name)
            continue
        openupgrade.add_xmlid(
            env.cr,
            "partner_compassion",
            xmlid,
            "advocate.engagement",
            row[0],
            noupdate=True,
        )
        _logger.info("T2740: %s engagement %s adopted", name, row[0])
