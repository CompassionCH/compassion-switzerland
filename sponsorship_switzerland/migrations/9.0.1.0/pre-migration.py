# -*- encoding: utf-8 -*-
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

    # Inactive old payment modes
    cr.execute("""
        UPDATE account_payment_mode SET active = false;
    """)

    # Configure journals
    cr.execute("""
    INSERT INTO account_journal_inbound_payment_method_rel (journal_id,
    inbound_payment_method)
    VALUES
      (219, (SELECT id FROM account_payment_method WHERE code = 'lsv')),
      (212, (SELECT id FROM account_payment_method WHERE code = 'sepa.ch.dd'))
    """)
