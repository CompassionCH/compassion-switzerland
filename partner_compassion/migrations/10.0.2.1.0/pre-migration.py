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
from openupgradelib import openupgrade


def migrate(cr, version):
    if not version:
        return

    # Move xml records of shared_inbox_switzerland module
    openupgrade.rename_xmlids(cr, [
        ('shared_inbox_switzerland.mail_alias_info',
         'partner_compassion.mail_alias_info'),
    ])
    cr.execute("""
        DELETE FROM ir_model_data
        WHERE module = 'shared_inbox_switzerland';
    """)
