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

    one_day_reminder_config = env['partner.communication.config'].search([
        ('name', 'ilike', '1 Day Birthday Reminder')
    ])
    if one_day_reminder_config:
        openupgrade.add_xmlid(
            env.cr,
            module='partner_communication_switzerland',
            xmlid='birthday_remainder_1day_before',
            model='partner.communication.config',
            res_id=one_day_reminder_config.id,
            noupdate=True
        )
