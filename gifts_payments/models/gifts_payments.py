from odoo import models, fields, api, exceptions
import re


class GiftsPayments(models.TransientModel):
    _name = 'gifts.payments'

    gifts_ids_text = fields.Text('Gifts IDs')

    @api.multi
    def do_gifts_search(self):
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'gifts.results',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': str({'gifts_list': self.gifts_ids_text,
                            'move_id': self.move_id.id})
        }

    move_id = fields.Many2one('account.move', string='Journal Entry',
                              ondelete="cascade",
                              help="The move of this entry line.", index=True,
                              required=True, auto_join=True)


class GiftsPaymentsResults(models.TransientModel):
    _name = 'gifts.results'

    info = fields.Text('Ceci est un test')

    @api.model
    def _move_lines_gifts(self):
        accounts = self.env['account.account']
        move = self.env['account.move'].search([
            ('id', '=', self._context['move_id'])])

        ids = re.findall('[0-9]{3,6}', self._context['gifts_list'])
        gifts = self.env['sponsorship.gift'].search([('id', 'in', ids)])
        for gift in gifts:
            if not gift.gmc_gift_id:
                raise exceptions.AccessError(
                    'Gift with global_id '+str(gift.id)+' has no gmc_gift_id')

        move_lines = gifts.mapped('payment_id.line_ids').filtered(
            lambda r: r.account_id.code == '2002')

        debit = {
            'name': 'gift',
            'ref': move.ref,
            'journal_id': move.journal_id.id,
            'currency_id': gifts.mapped('currency_usd').id,
            'credit': 0.0,
            'debit': sum(gifts.mapped('amount')),
            'date': move.date,
            'date_maturity': move.date,
            'amount_currency': sum(gifts.mapped('amount_us_dollars')),
            'partner_id': move.partner_id.id,
            'move_id': move.id,
            'account_id': move_lines.mapped('account_id').id,
        }

        credit = debit.copy()
        credit['debit'] = 0.0
        credit['credit'] = debit['debit']
        credit['amount_currency'] = debit['amount_currency']*-1
        credit['account_id'] = accounts.search([('code', '=', '2001')]).id

        #  write new lines in move
        move.write({'line_ids': [(0, 0, debit), (0, 0, credit)]})

        new_lines = move.line_ids.sorted('create_date')[-2:]
        line_id = new_lines.filtered(lambda r: r.account_id.code == '2002').id

        to_reconcile_list = move_lines.mapped('id')
        to_reconcile_list.append(line_id)
        to_reconcile = self.env['account.move.line'].browse(to_reconcile_list)

        return to_reconcile

    @api.multi
    def do_gifts_reconciliation(self):
        return self.move_lines_gifts.reconcile()

    move_lines_gifts = fields.Many2many(comodel_name='account.move.line',
                                        string='Gifts paid',
                                        default=_move_lines_gifts)
