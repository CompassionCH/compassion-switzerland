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

    old_sponsor = env.ref('partner_compassion.res_partner_category_old')
    sponsor = env.ref('partner_compassion.res_partner_category_sponsor')
    church = env.ref('partner_compassion.res_partner_category_church')
    env['res.partner'].search([
        ('category_id', 'in', (old_sponsor + sponsor + church).ids)
    ]).update_number_sponsorships()
