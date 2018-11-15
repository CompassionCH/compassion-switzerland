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

    # Convert event types
    sport = env.ref('website_event_compassion.event_type_sport').id
    stand = env.ref('website_event_compassion.event_type_stand').id
    concert = env.ref('website_event_compassion.event_type_concert').id
    pres = env.ref('website_event_compassion.event_type_presentation').id
    meeting = env.ref('website_event_compassion.event_type_meeting').id
    group = env.ref('website_event_compassion.event_type_group_visit').id
    type_mapping = {}

    for event in env['crm.event.compassion'].search([]):
        if event.type == 'sport':
            type_mapping[event.id] = sport
        elif event.type == 'stand':
            type_mapping[event.id] = stand
        elif event.type == 'concert':
            type_mapping[event.id] = concert
        elif event.type == 'presentation':
            type_mapping[event.id] = pres
        elif event.type == 'meeting':
            type_mapping[event.id] = meeting
        elif event.type == 'tour':
            type_mapping[event.id] = group

    for event_id, type_id in type_mapping.iteritems():
        env.cr.execute("""
            UPDATE crm_event_compassion
            SET event_type_id = %s
            WHERE id = %s
        """, [type_id, event_id])

    # Put random uuid on registrations
    for registration in env['event.registration'].search([]):
        registration.uuid = registration._get_uuid()
