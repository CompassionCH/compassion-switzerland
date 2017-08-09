# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Remove data to avoid record deletion
    cr.execute("""
      UPDATE ir_model_data
      SET model='account.operation.template'
      WHERE module = 'account_reconcile_compassion'
      AND model='account.statement.operation.template'
    """)
