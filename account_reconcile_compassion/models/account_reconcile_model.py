from odoo import api, models, _
from odoo.exceptions import UserError


class AccountReconcileModel(models.Model):
    _inherit = "account.reconcile.model"

    @api.model
    def product_changed(self, product_id):
        """
        Helper to get the account and analytic account in reconcile view.
        :param product_id:
        :return: account_id, analytic_id
        """
        res = super().product_changed(product_id)
        if product_id and product_id['product_id']:
            analytic_id = (
                self.env["account.analytic.default"]
                    .account_get(product_id['product_id'])
                    .analytic_id.id
            )
            res["analytic_id"] = analytic_id
        return res

    @api.multi
    def _get_invoice_matching_query(self, st_lines, excluded_ids=None,
                                    partner_map=None):
        # Since this is source-code copied, we won't check pylint
        # pylint: disable=W1401
        ''' Get the query applying all rules trying to match existing entries with
        the given statement lines.
        :param st_lines:        Account.bank.statement.lines recordset.
        :param excluded_ids:    Account.move.lines to exclude.
        :param partner_map:     Dict mapping each line with new partner eventually.
        :return:                (query, params)
        '''
        # CODE COPIED FROM ODOO SOURCE BUT WE REMOVE SOME PART OF THE QUERY WHICH
        # IS VERY SLOW
        if any(m.rule_type != 'invoice_matching' for m in self):
            raise UserError(_(
                'Programmation Error: Can\'t call _get_invoice_matching_query() for '
                'different rules than \'invoice_matching\''))

        queries = []
        all_params = []
        for rule in self:
            # N.B: 'communication_flag' is there to distinguish invoice matching
            # through the number/reference
            # (higher priority) from invoice matching using the partner (lower
            # priority).
            query = '''
                SELECT
                    %s                                  AS sequence,
                    %s                                  AS model_id,
                    st_line.id                          AS id,
                    aml.id                              AS aml_id,
                    aml.currency_id                     AS aml_currency_id,
                    aml.date_maturity                   AS aml_date_maturity,
                    aml.amount_residual                 AS aml_amount_residual,
                    aml.amount_residual_currency        AS aml_amount_residual_currency,
                    aml.balance                         AS aml_balance,
                    aml.amount_currency                 AS aml_amount_currency,
                    account.internal_type               AS account_internal_type,

                    -- Determine a matching or not with the statement line
                    -- communication using the move.name or move.ref.
                    -- only digits are considered and reference are split by any
                    -- space characters
                    regexp_split_to_array(substring(REGEXP_REPLACE(move.name,
                    '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'), '\s+')
                    && regexp_split_to_array(substring(REGEXP_REPLACE(st_line.name,
                    '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'), '\s+')
                    OR
                    (
                        move.ref IS NOT NULL
                        AND
                            regexp_split_to_array(substring(REGEXP_REPLACE(move.ref,
                            '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'), '\s+')
                            &&
                            regexp_split_to_array(substring(REGEXP_REPLACE(
                            st_line.name, '[^0-9|^\s]', '', 'g'), '\S(?:.*\S)*'), '\s+')
                    )                                   AS communication_flag
                FROM account_bank_statement_line st_line
                LEFT JOIN account_journal journal       ON journal.id =
                st_line.journal_id
                LEFT JOIN jnl_precision
                    ON jnl_precision.journal_id = journal.id
                LEFT JOIN res_company company
                    ON company.id = st_line.company_id
                LEFT JOIN partners_table line_partner
                    ON line_partner.line_id = st_line.id
                , account_move_line aml
                LEFT JOIN account_move move             ON move.id = aml.move_id
                LEFT JOIN account_account account       ON account.id = aml.account_id
                WHERE st_line.id IN %s
                    AND aml.company_id = st_line.company_id
                    AND (
                            -- the field match_partner of the rule might enforce the
                            -- second part of
                            -- the OR condition, later in _apply_conditions()
                            line_partner.partner_id = 0
                            OR
                            aml.partner_id = line_partner.partner_id
                        )
                    AND CASE WHEN st_line.amount > 0.0
                             THEN aml.balance > 0
                             ELSE aml.balance < 0
                        END

                    -- if there is a partner, propose all aml of the partner,
                    -- otherwise propose only the ones
                    -- matching the statement line communication
                    AND
                    (
                        (
                            line_partner.partner_id != 0
                            AND
                            aml.partner_id = line_partner.partner_id
                        )
                     -- HERE WE REMOVED THE "OR" PART
                    )
                    AND
                    (
                        (
                        -- blue lines appearance conditions
                        aml.account_id IN (journal.default_credit_account_id,
                        journal.default_debit_account_id)
                        AND aml.statement_id IS NULL
                        AND (
                            company.account_bank_reconciliation_start IS NULL
                            OR
                            aml.date > company.account_bank_reconciliation_start
                            )
                        )
                        OR
                        (
                        -- black lines appearance conditions
                        account.reconcile IS TRUE
                        AND aml.reconciled IS FALSE
                        )
                    )
                '''
            # Filter on the same currency.
            if rule.match_same_currency:
                query += '''
                        AND COALESCE(st_line.currency_id, journal.currency_id,
                        company.currency_id) = COALESCE(aml.currency_id,
                        company.currency_id)
                    '''

            params = [rule.sequence, rule.id, tuple(st_lines.ids)]
            # Filter out excluded account.move.line.
            if excluded_ids:
                query += 'AND aml.id NOT IN %s'
                params += [tuple(excluded_ids)]
            query, params = rule._apply_conditions(query, params)
            queries.append(query)
            all_params += params
        full_query = self._get_with_tables(st_lines, partner_map=partner_map)
        full_query += ' UNION ALL '.join(queries)
        # Oldest due dates come first.
        full_query += ' ORDER BY aml_date_maturity, aml_id'
        return full_query, all_params
