# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    # Convert contracts
    cr.execute("""
    UPDATE recurring_contract_group c
    SET payment_mode_id = (
      SELECT max(id) FROM account_payment_mode
      WHERE name = (SELECT name FROM account_payment_term WHERE id =
                    c.payment_term_id)
    )
    """)
    cr.execute("""
        UPDATE recurring_contract c
        SET payment_mode_id = (
          SELECT max(id) FROM account_payment_mode
          WHERE name = (SELECT name FROM account_payment_term WHERE id =
                        c.payment_term_id)
        )
    """)

    # Convert open invoices payment_modes
    cr.execute("""
UPDATE account_invoice i
SET payment_mode_id = (
  SELECT max(id) FROM account_payment_mode
  WHERE name = (SELECT name FROM account_payment_term WHERE id =
                i.payment_term_id)
), mandate_id = (
  SELECT max(id) FROM account_banking_mandate WHERE
  partner_id = i.partner_id AND state = 'valid'
)
WHERE state = 'open' AND type = 'out_invoice'
    """)
    cr.execute("""
    UPDATE account_move_line i
    SET payment_mode_id = (
      SELECT payment_mode_id FROM account_invoice
      WHERE move_id = i.move_id
    ),
    mandate_id = (
      SELECT mandate_id FROM account_invoice
      WHERE move_id = i.move_id
    )
    WHERE move_id IN (
      SELECT move_id FROM account_invoice WHERE state = 'open' AND type =
      'out_invoice') AND debit > 0
        """)

    # Add Completion Rules
    cr.execute("""
    INSERT INTO account_journal_account_statement_completion_rule_rel
    (account_journal_id, account_statement_completion_rule_id)
    VALUES (236, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'get_from_partner_ref')),
           (236, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'get_from_bvr_ref')),
           (236, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'get_from_move_line_ref')),
           (237, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'lsv_dd_get_from_bvr_ref')),
           (234, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'lsv_dd_get_from_bvr_ref')),
           (212, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'get_from_amount')),
           (212, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'get_from_lsv_dd')),
           (212, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'get_sponsor_name')),
           (219, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'get_from_amount')),
           (219, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'get_from_lsv_dd')),
           (219, (SELECT id from account_statement_completion_rule WHERE
                  function_to_call = 'get_sponsor_name'))
    """)
