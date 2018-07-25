# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    env.cr.execute("""
        SELECT c.id
        FROM partner_communication_config c
            JOIN utm_source s ON c.source_id = s.id
        WHERE s.name ILIKE '%1 Day Birthday Reminder%'
    """)
    one_day_reminder_config = env.cr.fetchone()
    if one_day_reminder_config:
        openupgrade.add_xmlid(
            env.cr,
            module='partner_communication_switzerland',
            xmlid='birthday_remainder_1day_before',
            model='partner.communication.config',
            res_id=one_day_reminder_config[0],
            noupdate=True
        )

    env.cr.execute("""
        SELECT id
        FROM mail_template
        WHERE name ILIKE '%1 Day Birthday Reminder%'
    """)
    one_day_reminder_template = env.cr.fetchone()
    if one_day_reminder_template:
        openupgrade.add_xmlid(
            env.cr,
            module='partner_communication_switzerland',
            xmlid='email_sponsorship_birthday_1day_reminder',
            model='mail.template',
            res_id=one_day_reminder_template[0],
            noupdate=True
        )
