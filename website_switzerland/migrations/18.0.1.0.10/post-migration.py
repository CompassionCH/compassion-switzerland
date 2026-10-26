import logging

from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)

# Privacy notice of Compassion Switzerland, per language: the /legal route of
# this module redirected to it, my_compassion's /legal now redirects to the
# Privacy Policy URL of the website.
PRIVACY_POLICY_URLS = {
    "en_US": "https://compassion.ch/protection-des-donnees/",
    "fr_CH": "https://compassion.ch/protection-des-donnees/",
    "de_DE": "https://compassion.ch/de/datenschutz/",
    "it_IT": "https://compassion.ch/it/privacy-e-termini/",
}


@openupgrade.migrate()
def migrate(env, version):
    """Set the Swiss privacy notice on the Swiss websites, for the languages
    that have none (all but MyCompassion), keeping the values already set."""
    websites = (
        env["website"]
        .search([])
        .filtered(lambda w: w.company_id.partner_id.country_id.code == "CH")
    )
    if not websites:
        return
    # The stored translations: reading the field in a language without one
    # returns the English value.
    env.cr.execute(
        "SELECT id, privacy_policy_url FROM website WHERE id IN %s",
        [tuple(websites.ids)],
    )
    stored = {row[0]: row[1] or {} for row in env.cr.fetchall()}
    for website in websites:
        missing = {
            lang: url
            for lang, url in PRIVACY_POLICY_URLS.items()
            if not stored[website.id].get(lang)
        }
        if not missing:
            continue
        if "en_US" in missing:
            website.with_context(lang="en_US").privacy_policy_url = missing["en_US"]
        others = {lang: url for lang, url in missing.items() if lang != "en_US"}
        if others:
            website.update_field_translations("privacy_policy_url", others)
        _logger.info(
            "Website %s: privacy policy URL set for %s", website.id, sorted(missing)
        )
