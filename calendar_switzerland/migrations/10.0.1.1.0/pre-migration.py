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

    # Attach flyer in post record
    env.cr.execute("""
        SELECT id FROM calendar_event_type
        WHERE name = 'flyer in post'
    """)
    res_id = env.cr.fetchone()[0]
    openupgrade.add_xmlid(
        env.cr, 'calendar_switzerland', 'calendar_event_flyer',
        'calendar.event.type', res_id, noupdate=True
    )
