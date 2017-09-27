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
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    cr = env.cr
    # Install dependency
    openupgrade.logged_query(cr, """
        UPDATE ir_module_module
        SET state='to install'
        WHERE name = 'account_statement_completion' AND state='uninstalled';
    """)

    # Inactive old payment modes
    openupgrade.logged_query(cr, """
        UPDATE account_payment_mode SET active = false;
    """)

    # Configure journals
    openupgrade.logged_query(cr, """
    INSERT INTO account_journal_inbound_payment_method_rel (journal_id,
    inbound_payment_method)
    VALUES
      (219, (SELECT max(id) FROM account_payment_method WHERE code = 'lsv')),
      (212, (SELECT max(id) FROM account_payment_method WHERE code = 'sepa.ch.dd'))
    """)
