import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """The "Speaker Translator" advocate.engagement record used to only
    exist as a database-only row with no xmlid (created directly via the
    UI). It's now shipped as real module data
    (data/advocate_engagement_data.xml, id engagement_speaker_translator).

    This must run as a PRE-migration: if any pre-existing "Speaker
    Translator" row already exists in this database, adopt it under that
    same xmlid *before* the module's data file loads, so Odoo's data
    loader recognizes the xmlid already exists and reuses this row
    instead of creating a duplicate empty one alongside it (and any
    advocate already tagged with the old row keeps that tag intact).

    Matches the name across all translations (not just en_US) via raw
    SQL, to maximize the chance of finding the existing row regardless
    of which language it happens to be stored under.
    """
    env.cr.execute(
        """
        SELECT id FROM advocate_engagement
        WHERE name::text ILIKE %s
        LIMIT 1
        """,
        ("%Speaker Translator%",),
    )
    row = env.cr.fetchone()
    if not row:
        _logger.info(
            "No pre-existing 'Speaker Translator' advocate.engagement row "
            "found in this database; the new module data record will be "
            "created fresh."
        )
        return
    openupgrade.add_xmlid(
        env.cr,
        "partner_compassion",
        "engagement_speaker_translator",
        "advocate.engagement",
        row[0],
        noupdate=True,
    )
