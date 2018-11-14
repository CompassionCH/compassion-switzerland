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


def migrate(cr, version):
    if not version:
        return

    # Prepares column event_type_id to be required by setting default value
    cr.execute("""
ALTER TABLE crm_event_compassion
ADD COLUMN event_type_id INTEGER;

UPDATE crm_event_compassion
SET event_type_id = 1;
    """)
