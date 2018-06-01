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
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Create ambassador details for old ambassadors
    ambassadors = env['res.partner'].search([
        ('quote_migrated', '=', True)
    ])
    for ambassador in ambassadors:
        ambassador.ambassador_details_id = env['ambassador.details'].create({
            'partner_id': ambassador.id,
            'quote': ambassador.ambassador_quote
        })
