# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Remove registration task for emergency contact, as its' filled at the
    # same time than the passport.
    cr.execute("""
    DELETE FROM event_registration_task
    WHERE name = 'Fill emergency contact';
    """)
