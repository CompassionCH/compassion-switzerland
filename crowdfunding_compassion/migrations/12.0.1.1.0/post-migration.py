import logging
from openupgradelib import openupgrade

_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Migrate missing campaigns on donations
    mass_mailing_medium = env.ref("recurring_contract.utm_medium_mass_mailing")
    donations = env["account.invoice.line"].search([
        ("medium_id", "=", mass_mailing_medium.id),
        ("source_id", "!=", False),
        "|", ("account_analytic_id", "=", False),
        ("account_analytic_id.campaign_id", "=", False)
    ])
    _logger.info("Fixing %s donations by restoring the campaign...", len(donations))
    fixed = 0
    for donation in donations:
        mass_mailing = env["mail.mass_mailing"].search([
            ("source_id", "=", donation.source_id.id)], limit=1)
        if mass_mailing:
            campaign = mass_mailing.mass_mailing_campaign_id.campaign_id
            analytic = env["account.analytic.account"].search([
                ("campaign_id", "=", campaign.id)], limit=1)
            if not analytic:
                analytic = analytic.create({
                    "name": campaign.name,
                    "campaign_id": campaign.id
                })
            donation.account_analytic_id = analytic
            fixed += 1
    _logger.info("Successfully fixed %s donations", fixed)
