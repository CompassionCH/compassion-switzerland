# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from odoo import api, fields, models


class AccountStatement(models.Model):
    """ Adds a relation to a recurring invoicer. """

    _inherit = 'account.bank.statement'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    invoice_ids = fields.Many2many(
        'account.invoice', string='Invoices', compute='_compute_invoices'
    )
    generated_invoices_count = fields.Integer(
        'Invoices', compute='_compute_invoices')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    @api.multi
    def _compute_invoices(self):
        invoice_obj = self.env['account.invoice']
        for stmt in self:
            invoices = invoice_obj.search([('origin', '=', stmt.name)])
            stmt.invoice_ids = invoices
            stmt.generated_invoices_count = len(invoices)

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    @api.multi
    def to_invoices(self):
        self.ensure_one()
        return {
            'name': 'Generated Invoices',
            'view_mode': 'tree,form',
            'view_type': 'form',
            'res_model': 'account.invoice',
            'domain': [('origin', '=', self.name)],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': {'form_view_ref': 'account.invoice_form',
                        'journal_type': 'sale'},
        }

    @api.multi
    def unlink(self):
        self.mapped('invoice_ids').filtered(
            lambda i: i.state in ('draft', 'open')
        ).action_invoice_cancel()
        return super(AccountStatement, self).unlink()
