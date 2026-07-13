import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    """The "Speaker Translator" advocate.engagement record was created
    directly in the database (no xmlid), so code had to match it by name
    (in a fixed language context) to route it to the translation-volunteer
    recipient in advocate_cron. That's fragile: if the record's name
    doesn't have a clean en_US translation in a given environment, the
    match silently fails and those advocates fall back to language-based
    routing instead (flagged in T1228 PR review). Giving it a real xmlid
    here lets the code reference it by id via env.ref() instead."""
    engagement = (
        env["advocate.engagement"]
        .with_context(lang="en_US")
        .search([("name", "=", "Speaker Translator")], limit=1)
    )
    if not engagement:
        _logger.info(
            "No 'Speaker Translator' advocate.engagement record found in "
            "this database, nothing to give an xmlid to."
        )
        return
    openupgrade.add_xmlid(
        env.cr,
        "partner_compassion",
        "engagement_speaker_translator",
        "advocate.engagement",
        engagement.id,
        noupdate=True,
    )
