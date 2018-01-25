# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        SELECT id FROM utm_medium WHERE name = 'Mass mailing'
    """)
    mass_mailing_medium = cr.fetchone()[0]
    cr.execute("""
        SELECT c.campaign_id, %s, r.id 
        FROM recurring_contract r JOIN mail_mass_mailing_campaign c
        ON r.mailing_campaign_id = c.id 
        WHERE r.mailing_campaign_id IS NOT NULL
    """, [mass_mailing_medium])
    results = cr.fetchall()
    for row in results:
        cr.execute("""
            UPDATE recurring_contract
            SET campaign_id = %s, medium_id = %s
            WHERE id = %s
        """, row)

    cr.execute("""
        ALTER TABLE account_invoice ADD COLUMN campaign_bkp INTEGER;
        ALTER TABLE correspondence ADD COLUMN campaign_bkp INTEGER;
        UPDATE account_invoice SET campaign_bkp = mailing_campaign_id;
        UPDATE correspondence SET campaign_bkp = mailing_campaign_id;
    """)

    # Delete view which is making errors at migration
    cr.execute("""
        DELETE FROM ir_ui_view
        WHERE model='recurring.contract' AND arch_db LIKE '%web_data%'
    """)
