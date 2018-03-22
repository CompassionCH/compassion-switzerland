# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class AccountStatement(models.Model):
    """ Adds a relation to a recurring invoicer. """

    _inherit = 'account.bank.statement'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    name = fields.Char(
        default=lambda b: b._default_name()
    )

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _default_name(self):
        """ Find the appropriate sequence """
        journal_id = self.env.context.get('default_journal_id')
        if journal_id:
            journal = self.env['account.journal'].browse(journal_id)
            sequence = self.env['ir.sequence'].search([
                ('name', '=', journal.name)])
            if sequence:
                return sequence.next_by_id()
        return ''

    @api.multi
    def reconciliation_widget_preprocess(self):
        """ Overwrite with slight changes
            odoo/addons/account/models/accound_bank_statement.py

            Get statement lines of the specified statements or all
            unreconciled statement lines and try to automatically reconcile
            them / find them a partner.
            Return ids of statement lines left to reconcile and other data
            for the reconciliation widget.
        """
        statements = self
        # NB : The field account_id can be used at the statement line
        # creation/import to avoid the reconciliation process on it later on,
        # this is why we filter out statements lines where account_id is set

        sql_query = """SELECT stl.id
                        FROM account_bank_statement_line AS stl
                        JOIN res_partner AS partner ON partner.id =
                        stl.partner_id
                        WHERE stl.account_id IS NULL AND not exists (select 1
                        from account_move m where m.statement_line_id = stl.id)
                            AND stl.company_id = %s
                """
        params = (self.env.user.company_id.id,)
        if statements:
            sql_query += ' AND stl.statement_id IN %s'
            params += (tuple(statements.ids),)
        sql_query += ' ORDER BY partner.lastname, partner.firstname, ' \
                     'partner.id'
        self.env.cr.execute(sql_query, params)
        x = self.env.cr.dictfetchall()
        lines_left = self.env['account.bank.statement.line'].browse([
            line.get('id') for line in x])
        # try to assign partner to bank_statement_line
        stl_to_assign_partner = [stl.id for stl in lines_left if not
                                 stl.partner_id]
        refs = list(set([st.name for st in lines_left if not
                         stl.partner_id]))
        if lines_left and stl_to_assign_partner and refs \
                and lines_left[0].journal_id.default_credit_account_id \
                and lines_left[0].journal_id.default_debit_account_id:

            sql_query = """SELECT aml.partner_id, aml.ref, stl.id
                            FROM account_move_line aml
                                JOIN account_account acc ON acc.id =
                                aml.account_id
                                JOIN account_bank_statement_line stl ON
                                aml.ref = stl.name
                                JOIN res_partner AS partner ON partner.id =
                        stl.partner_id
                            WHERE (aml.company_id = %s
                                AND aml.partner_id IS NOT NULL)
                                AND (
                                    (aml.statement_id IS NULL AND
                                    aml.account_id IN %s)
                                    OR
                                    (acc.internal_type IN ('payable',
                                    'receivable') AND aml.reconciled = false)
                                    )
                                AND aml.ref IN %s
                                """
            params = (self.env.user.company_id.id,
                      (lines_left[0].journal_id.default_credit_account_id.id,
                       lines_left[0].journal_id.default_debit_account_id.id),
                      tuple(refs))
            if statements:
                sql_query += 'AND stl.id IN %s'
                params += (tuple(stl_to_assign_partner),)
            sql_query += ' ORDER BY partner.lastname, partner.firstname, ' \
                         'partner.id'
            self.env.cr.execute(sql_query, params)
            results = self.env.cr.dictfetchall()
            st_line = self.env['account.bank.statement.line']
            for line in results:
                st_line.browse(line.get('id')).write(
                    {'partner_id': line.get('partner_id')})
        return {
            'st_lines_ids': lines_left.ids,
            'notifications': [],
            'statement_name':
                len(statements) == 1 and statements[0].name or False,
            'num_already_reconciled_lines': 0,
        }
