##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Put back utm_campaign in invoice and correspondence objects
    mass_mailing_medium = env.ref(
        'contract_compassion.utm_medium_mass_mailing')
    env.cr.execute("""
        SELECT id, campaign_bkp
        FROM account_invoice
        WHERE campaign_bkp IS NOT NULL
    """)
    results = env.cr.fetchall()
    for row in results:
        campaign = env['mail.mass_mailing.campaign'].browse(row[1])
        env['account.invoice'].browse(row[0]).write({
            'campaign_id': campaign.campaign_id.id,
            'medium_id': mass_mailing_medium.id
        })

    env.cr.execute("""
            SELECT id, campaign_bkp
            FROM correspondence
            WHERE campaign_bkp IS NOT NULL
        """)
    results = env.cr.fetchall()
    for row in results:
        campaign = env['mail.mass_mailing.campaign'].browse(row[1])
        env['correspondence'].browse(row[0]).write({
            'campaign_id': campaign.campaign_id.id,
            'medium_id': mass_mailing_medium.id
        })

    env.cr.execute("""
        ALTER TABLE account_invoice DROP COLUMN campaign_bkp;
        ALTER TABLE correspondence DROP COLUMN campaign_bkp;
    """)
