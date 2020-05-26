# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Joel Vaucher <jvaucher@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, fields, models


class SearchBankAddressWizard(models.TransientModel):
    _name = 'search.bank.address.wizard'

    account_bank_statement_line = fields.Many2one(
        'account.bank.statement.line',
        domain=lambda self: self._get_domain(),
        default=lambda self: self._get_default())
    partner_address = fields.Char(
        'Partner address (Maybe)',
        related='account_bank_statement_line.partner_address',
        readonly=True)
    date = fields.Date(
        'Last time used',
        related='account_bank_statement_line.date',
        readonly=True)

    overwriting_street = fields.Char('Street', default="")
    overwriting_better_zip_id = fields.Many2one('res.better.zip',
                                                'City/Location')

    @api.model
    def _get_domain(self):
        partner_id = self.env.context.get('active_id')
        if partner_id:
            return [('partner_id', '=', partner_id),
                    ('partner_address', '!=', False)]
        return []

    @api.model
    def _get_default(self):
        return self.env['account.bank.statement.line']\
            .search(self._get_domain(), order='date desc', limit=1)

    @api.multi
    def change_address(self):
        self.env['res.partner'].browse(self.env.context['active_id']).write({
            'street': self.overwriting_street,
            'zip': self.overwriting_better_zip_id.zip_type,
            'state_id': self.overwriting_better_zip_id.state_id.id,
            'country_id': self.overwriting_better_zip_id.country_id.id,
        })
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def cancel_change(self):
        return {'type': 'ir.actions.act_window_close'}
