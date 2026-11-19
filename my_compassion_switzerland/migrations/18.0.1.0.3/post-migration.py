##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

SWISS_FOOTER_LINKS = {
    "privacy_policy_url": "https://compassion.ch/protection-des-donnees/",
    "social_facebook": "https://www.facebook.com/compassionschweiz",
    "social_instagram": "https://www.instagram.com/compassionswiss",
    "social_youtube": "https://www.youtube.com/channel/UChVNRRvihHG0AYPsdEFfasQ",
    "social_vimeo": "https://vimeo.com/compassionswitzerland",
    "social_linkedin": (
        "https://www.linkedin.com/company/compassion-schweiz-suisse-svizzera"
    ),
}


def migrate(cr, version):
    """The theme footer now renders its links from website fields; write the
    values it used to hardcode onto the websites carrying the theme, so the
    footer keeps rendering exactly the same links. Existing field values are
    overwritten on purpose: the theme footer replaces the stock footer, so
    nothing rendered these fields on those websites before and any stored
    value was invisible stale data.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    theme = env["ir.module.module"].search(
        [("name", "=", "theme_compassion_2025")], limit=1
    )
    if not theme:
        return
    websites = env["website"].search([("theme_id", "=", theme.id)])
    if websites:
        websites.write(SWISS_FOOTER_LINKS)
        _logger.info("Seeded the Swiss footer links on websites %s.", websites.ids)
