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

    # Convert Muskathlon event types
    muskathlon = env.ref('muskathlon.event_type_muskathlon').id
    env['crm.event.compassion'].search([
        ('type', '=', 'sport'),
        ('odoo_event_id', '!=', False)
    ]).write({'event_type_id': muskathlon})
    env['event.event'].search([]).write({'event_type_id': muskathlon})
