# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Move fields in module website_event_compassion
    openupgrade.update_module_moved_fields(
        env.cr, 'crm.event.compassion',
        ['website_description', 'picture_1', 'filename_1', 'registration_fee',
         'website_side_info'], 'muskathlon', 'website_event_compassion'
    )
