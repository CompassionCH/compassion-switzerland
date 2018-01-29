# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Fluckiger Nathan
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    cr = env.cr
    cr.execute("""
        UPDATE res_partner p SET number_sponsorships = (
            SELECT count(*)
            FROM recurring_contract c JOIN res_partner pp
              ON pp.id = c.partner_id
            WHERE pp.church_id = p.id
            AND c.child_id IS NOT NULL
            AND c.state = 'active'
        )
        WHERE p.is_church = TRUE
    """)
