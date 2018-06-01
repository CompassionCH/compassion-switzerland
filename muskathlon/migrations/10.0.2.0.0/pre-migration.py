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


def migrate(cr, version):
    if not version:
        return

    # Remove old view
    cr.execute("""
        DELETE FROM ir_ui_view WHERE arch_db LIKE '%ambassador_quote%'
         AND model='res.partner'
    """)
