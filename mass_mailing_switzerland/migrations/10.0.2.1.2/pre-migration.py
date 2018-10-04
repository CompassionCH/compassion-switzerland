# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Push UTM data from invoice to invoice_line
    cr.execute("""
        UPDATE account_invoice_line AS l
        SET source_id = i.source_id,
            campaign_id = i.campaign_id,
            medium_id = i.medium_id
        FROM account_invoice i
        WHERE l.invoice_id = i.id
    """)
