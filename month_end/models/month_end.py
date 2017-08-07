# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Maxime Beck
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import datetime
import calendar
from odoo import api, models, fields


class MonthEnd(models.Model):
    _name = 'month.end'

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def process_create_accounting_entry(self):
        date_format = '%d.%m.%Y'

        today = datetime.date.today()
        first_day = today.replace(day=1)
        last_day = today.replace(day=calendar.monthrange(today.year, today.month)[1])

        first_day_last_month = first_day.replace(month=today.month-1)
        last_day_last_month = last_day.replace(month=today.month-1)

        analytic_account_cd_pgm = self.env['account.analytic.account'].search([('name', '=', 'CD pgm')])
        partner_compassion_internationnal = self.env['res.partner'].search([('name', '=', 'Compassion Internationnal')])
        
        ## account_move_line entry
        # gift entry
        gift_account = self.env['account.account'].search([('code', '=', '2002')])
        montly_gifts = self.env['sponsorship.gift'].search(
            [
                ('state', '=', 'In Progress'),
                ('create_date', '>=', fields.Date.to_string(first_day)),
                ('create_date', '<=', fields.Date.to_string(last_day))
            ]
        )
        gift_name = 'gift invoice: ' + str(len(montly_gifts)) + ' gifts from ' + first_day.strftime(date_format) + ' to ' + last_day.strftime(date_format)
        gift_debit = 0
        for gift in montly_gifts:
            gift_debit += gift.amount
        gift_line_vals = {
            'account_id': gift_account.id,
            'name': gift_name,
            'debit': gift_debit,
            'partner_id': partner_compassion_internationnal.id
        }

        # sponsorship entry
        sponsorship_account = self.env['account.account'].search([('code', '=', '5000')])
        sponsorship_active = self.env['recurring.contract'].search_count([('child_id', '!=', False)])
        sponsorship_disbursed = self.env['recurring.contract'].search_count([('child_id.project_id.hold_cdsp_funds', '=', False)])
        sponsorship_name = str(sponsorship_active) + ' sponsorships, ' + \
                           str(sponsorship_disbursed) + ' disbursed'

        sponsorships = self.env['recurring.contract'].search([])
        sponsorship_debit = 0
        for sponsorship in sponsorships:
            for contract in sponsorship.contract_line_ids:
                sponsorship_debit += contract.amount

        sponsorship_line_vals = {
            'account_id': sponsorship_account.id,
            'name': sponsorship_name,
            'debit': sponsorship_debit,
            'analytic_account_id': analytic_account_cd_pgm.id,
            'partner_id': partner_compassion_internationnal.id
        }

        # USP entry
        usp_account = self.env['account.account'].search([('code', '=', '5017')])
        usps = self.env['account.move.line'].search(
            [
                ('account_id.code', '=', 5017),
                ('debit', '>', 0),
                ('date', '>=', fields.Date.to_string(first_day_last_month)),
                ('date', '<=', fields.Date.to_string(last_day_last_month))
            ]
        )
        usp_debit = 0
        for usp in usps:
            usp_debit += usp.debit
        usp_line_vals = {
            'account_id': usp_account.id,
            'name': 'disbursement',
            'debit': usp_debit,
            'analytic_account_id': analytic_account_cd_pgm.id,
            'partner_id': partner_compassion_internationnal.id
        }

        # balance entry
        balance_account = self.env['account.account'].search([('code', '=', '2001')])
        balance_name = 'disbursement'
        balance_credit = gift_debit + sponsorship_debit + usp_debit
        balance_line_vals = {
            'account_id': balance_account.id,
            'name': balance_name,
            'credit': balance_credit,
            'partner_id': partner_compassion_internationnal.id
        }

        ## account_move entry
        journal = self.env['account.journal'].search([('code', '=', 'OD')])[0]
        ref = today.strftime('%B %Y') + ' disbursement'
        date = today

        move_vals = {
            'name': 'Décompte de fin de mois',
            'state': 'posted',
            'journal_id': journal.id,
            'ref': ref,
            'date': date,
            'line_ids': [(0, 0, gift_line_vals), (0, 0, sponsorship_line_vals), (0, 0, usp_line_vals), (0, 0, balance_line_vals)],
        }
        self.env['account.move'].create(move_vals)
        return True