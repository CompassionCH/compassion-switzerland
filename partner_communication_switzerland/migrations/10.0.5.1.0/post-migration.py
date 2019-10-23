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

    # Put all communications to standard thank you rules
    thankyou_standard = env.ref('thankyou_letters.config_thankyou_standard')
    event_standard = env.ref(
        'partner_communication_switzerland.config_event_standard')
    env.cr.execute("""
        UPDATE partner_communication_job
        SET config_id = %s
        WHERE config_id IN (49, 51) -- old configs for small and large
""", [thankyou_standard.id])
    env.cr.execute("""
            UPDATE partner_communication_job
            SET config_id = %s
            WHERE config_id IN (52, 54) -- old configs for small and large
    """, [event_standard.id])
    env.cr.execute("""
        DELETE FROM partner_communication_config
        WHERE id IN (49, 51, 52, 54);
    """)

    # Create thank you configurations for the different amounts
    christian = env['res.users'].search([
        ('name', 'like', 'Willi Christian')
    ], limit=1)
    rachel = env['res.users'].search([
        ('name', 'like', 'Maglo Rachel')
    ], limit=1)
    env['thankyou.config'].create({
        'min_donation_amount': 0,
        'send_mode': 'digital',
        'user_id': rachel.id
    })
    env['thankyou.config'].create({
        'min_donation_amount': 100,
        'send_mode': 'physical',
        'user_id': rachel.id
    })
    env['thankyou.config'].create({
        'min_donation_amount': 1000,
        'send_mode': 'physical',
        'user_id': christian.id,
        'need_call': 'after_sending'
    })
