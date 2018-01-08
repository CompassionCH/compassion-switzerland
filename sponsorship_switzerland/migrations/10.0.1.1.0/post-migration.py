# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
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

    sponsor_cat_id = env['res.partner.category'].search([
        ('name', '=', 'Sponsor')
    ]).id
    old_sponsor_cat_id = env['res.partner.category'].search([
        ('name', '=', 'Old Sponsor')
    ]).id
    sponsors_and_old = env['res.partner'].search([
        ('category_id', '=', sponsor_cat_id),
        ('category_id', '=', old_sponsor_cat_id),
    ])
    sponsors_and_old.write({'category_id': [(3, old_sponsor_cat_id,)]})
