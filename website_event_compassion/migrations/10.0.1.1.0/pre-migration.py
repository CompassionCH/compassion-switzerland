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

    # Move fields from muskathlon module
    openupgrade.update_module_moved_fields(
        env.cr, 'crm.event.compassion', [
            'participants_amount_objective', 'thank_you_text',
        ],
        'muskathlon', 'website_event_compassion',
    )
    openupgrade.update_module_moved_fields(
        env.cr, 'event.registration', [
            'amount_objective',
            'website_published',
        ],
        'muskathlon', 'website_event_compassion'
    )
    openupgrade.update_module_moved_fields(
        env.cr, 'account.invoice.line', [
            'registration_id',
        ],
        'muskathlon', 'website_event_compassion'
    )
    openupgrade.update_module_moved_fields(
        env.cr, 'res.partner', [
            'registration_ids',
        ],
        'muskathlon', 'website_event_compassion'
    )
