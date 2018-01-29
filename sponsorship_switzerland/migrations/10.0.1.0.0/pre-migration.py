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
        SELECT id FROM account_journal
        WHERE code IN ('RCC', 'CPP')
    """)
    if cr.fetchall():
        openupgrade.add_xmlid(
            cr,
            'sponsorship_switzerland',
            'journal_raif',
            'account.journal',
            219,
            noupdate=True
        )
        openupgrade.add_xmlid(
            cr,
            'sponsorship_switzerland',
            'journal_post',
            'account.journal',
            212,
            noupdate=True
        )
