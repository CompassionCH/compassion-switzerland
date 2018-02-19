# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, exceptions, _


class MoveLine(models.Model):
    """ Adds a method to split a payment into several move_lines
    in order to reconcile only a partial amount, avoiding doing
    partial reconciliation. """
    _inherit = 'account.move.line'

    def split_payment_and_reconcile(self):
        residual = 0.0
        count_credit_lines = 0
        move = False
        move_line = False

        for line in self:
            residual += line.credit - line.debit
            if line.credit > 0:
                move = line.move_id
                move_line = line
                count_credit_lines += 1

        if residual <= 0:
            raise exceptions.UserError(
                _('This can only be done if credits > debits'))

        if count_credit_lines != 1:
            raise exceptions.UserError(
                _('This can only be done for one credit line'))

        # Edit move in order to split payment into two move lines
        move.button_cancel()
        move.write({
            'line_ids': [
                (1, move_line.id, {'credit': move_line.credit - residual}),
                (0, 0, {
                    'credit': residual,
                    'name': self.env.context.get('residual_comment',
                                                 move_line.name),
                    'account_id': move_line.account_id.id,
                    'date': move_line.date,
                    'date_maturity': move_line.date_maturity,
                    'journal_id': move_line.journal_id.id,
                    'partner_id': move_line.partner_id.id,
                }),
            ]
        })
        move.post()

        # Perform the reconciliation
        self.reconcile()

        return True
