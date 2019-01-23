# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
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

    # Activate travel features on youth trip and group visit
    travel_types = env['event.type'].search([
        ('name', 'in', ['Youth trip', 'Group visit'])]
    )
    travel_types.write({
        'travel_features': True
    })
    env['event.registration.stage'].search([
        ('name', 'in', [
            'Payment', 'Medical survey', 'Down payment', 'Sign Agreements',
        ])
    ]).write({'event_type_ids': [(6, 0, travel_types.ids)]})
