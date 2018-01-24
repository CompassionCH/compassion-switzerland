# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

def migrate(cr, version):
    if not version:
        return

    # Remove obsolete view
    cr.execute(
        "delete from ir_ui_view where arch_db like '%web_data%' "
        "and model='recurring.contract'"
    )
