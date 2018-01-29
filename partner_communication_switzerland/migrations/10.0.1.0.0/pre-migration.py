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
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    cr = env.cr
    cr.execute("""
        SELECT id FROM label_print
    """)
    if cr.fetchall():
        openupgrade.add_xmlid(
            cr,
            'partner_communication_switzerland',
            'label_print_sponsorship',
            'label.print',
            1,
            noupdate=True
        )
    cr.execute("""
            SELECT id FROM label_print_field
        """)
    if cr.fetchall():
        openupgrade.add_xmlid(
            cr,
            'partner_communication_switzerland',
            'label_print_field_ref',
            'label.print.field',
            1,
            noupdate=True
        )
        openupgrade.add_xmlid(
            cr,
            'partner_communication_switzerland',
            'label_print_field_sponsor_name',
            'label.print.field',
            2,
            noupdate=True
        )
        openupgrade.add_xmlid(
            cr,
            'partner_communication_switzerland',
            'label_print_field_child_name',
            'label.print.field',
            3,
            noupdate=True
        )
