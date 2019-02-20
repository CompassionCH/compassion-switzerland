# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Christopher Meier <dev@c-meier.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # id value for Doctor, Pastor, Professor, Miss
    # records don't exist anymore so we don't use env.ref to get their ids
    bad_ids = [7, 30, 45, 58]

    for partner in env['res.partner'].search([
        ("title.id", "in", bad_ids)
    ]):
        # 58 is id for Miss
        if partner.title.id == 58:
            partner.title = env.ref('base.res_partner_title_madam').id
        else:
            partner.title = env.ref('base.res_partner_title_mister').id
