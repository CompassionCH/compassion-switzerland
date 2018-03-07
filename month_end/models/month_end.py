# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import datetime
import calendar
from odoo import api, models, fields


class MonthEnd(models.AbstractModel):
    _name = 'month.end'

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def process_create_accounting_entry(self):
        date_format = '%d.%m.%Y'

        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year,
                                                         today.month)[1])

        last_month = (12 if today.month == 1 else today.month - 1)
        last_month_year = (today.year - 1 if today.month == 1 else today.year)
        first_day_last_month = first_day.replace(month=last_month,
                                                 year=last_month_year)
        last_day_last_month = last_day.replace(
            day=calendar.monthrange(today.year, last_month)[1],
            month=last_month,
            year=last_month_year
        )

        analytic_account_cd_pgm = self.env[
            'account.analytic.account'].search([('name', '=', 'CD pgm')])
        partner_compassion_internationnal = self.env[
            'res.partner'].search([('name', '=', 'Compassion '
                                                 'Internationnal')])

        # account_move_line entry
        # gift entry
        gift_account = self.env['account.account'].search([('code', '=',
                                                            '2002')])
        monthly_gifts = self.env['sponsorship.gift'].search(
            [
                ('state', '=', 'In Progress'),
                ('create_date', '>=', fields.Date.to_string(first_day)),
                ('create_date', '<=', fields.Date.to_string(last_day))
            ]
        )
        gift_name = 'gift invoice: ' + str(len(monthly_gifts)) + ' gifts ' \
                    'from ' + first_day.strftime(date_format) + ' to ' + \
                    last_day.strftime(date_format)
        gift_debit = sum(monthly_gifts.mapped('amount'))
        gift_line_vals = {
            'account_id': gift_account.id,
            'name': gift_name,
            'debit': gift_debit,
            'partner_id': partner_compassion_internationnal.id
        }

        # sponsorship entry
        sponsorship_account = self.env['account.account'].search(
            [('code', '=', '5000')]
        )
        sponsorship_active = self.env['recurring.contract'].search_count(
            [
                ('child_id', '!=', False),
                ('state', '=', 'active')
            ]
        )
        sponsorship_to_remove = self.env['recurring.contract'].search(
            [
                ('child_id.project_id.hold_cdsp_funds', '=', True),
                ('child_id', '!=', False),
                ('state', '=', 'active')
            ]
        )
        sponsorship_disbursed = sponsorship_active - sponsorship_to_remove

        sponsorship_name = \
            str(sponsorship_active) + ' sponsorships, ' + \
            str(len(sponsorship_disbursed)) + ' disbursed'

        sponsorship_debit = sum(sponsorship_disbursed.mapped(
            'contract_line_ids').filtered(
                lambda line: line.product_id.property_account_expense_id ==
                sponsorship_account
        ).mapped('subtotal'))
        sponsorship_line_vals = {
            'account_id': sponsorship_account.id,
            'name': sponsorship_name,
            'debit': sponsorship_debit,
            'analytic_account_id': analytic_account_cd_pgm.id,
            'partner_id': partner_compassion_internationnal.id
        }

        # USP entry
        usp_account = self.env['account.account'].search([('code', '=',
                                                           '5017')])
        usps = self.env['account.move.line'].search(
            [
                ('account_id.code', '=', 5017),
                ('debit', '>', 0),
                ('date', '>=', fields.Date.to_string(first_day_last_month)),
                ('date', '<=', fields.Date.to_string(last_day_last_month))
            ]
        )
        usp_debit = sum(usps.mapped('debit'))
        usp_line_vals = {
            'account_id': usp_account.id,
            'name': 'disbursement',
            'debit': usp_debit,
            'analytic_account_id': analytic_account_cd_pgm.id,
            'partner_id': partner_compassion_internationnal.id
        }

        # balance entry
        balance_account = self.env['account.account'].search([('code',
                                                               '=', '2001')])
        balance_name = 'disbursement'
        balance_credit = gift_debit + sponsorship_debit + usp_debit
        balance_line_vals = {
            'account_id': balance_account.id,
            'name': balance_name,
            'credit': balance_credit,
            'partner_id': partner_compassion_internationnal.id
        }

        # account_move entry
        journal = self.env['account.journal'].search([('code', '=', 'OD')])[0]
        ref = today.strftime('%B %Y') + ' disbursement'
        date = today

        move_vals = {
            'name': u'Décompte de fin de mois',
            'state': 'posted',
            'journal_id': journal.id,
            'ref': ref,
            'date': date,
            'line_ids': [
                (0, 0, gift_line_vals),
                (0, 0, sponsorship_line_vals),
                (0, 0, usp_line_vals),
                (0, 0, balance_line_vals)
            ],
        }
        self.env['account.move'].create(move_vals)
        return True
