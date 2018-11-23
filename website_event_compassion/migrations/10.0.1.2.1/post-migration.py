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


def migrate(cr, version):
    if not version:
        return

    # Force upgrade of communication data
    openupgrade.load_data(
        cr, 'website_event_compassion', 'data/group_visit_emails.xml',
    )
    openupgrade.load_data(
        cr, 'website_event_compassion', 'data/communication_config.xml',
    )
