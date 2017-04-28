# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.addons.sponsorship_compassion.models.product import \
    GIFT_CATEGORY, SPONSORSHIP_CATEGORY, FUND_CATEGORY

from openerp import api, models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_type = fields.Selection([
        ('sponsorship', 'Sponsorship'),
        ('gift', 'Gift'),
        ('fund', 'Fund donation'),
        ('other', 'Other'),
    ], compute='compute_invoice_type', store=True)
    last_payment = fields.Date(compute='compute_last_payment', store=True)

    @api.depends('invoice_line_ids', 'state')
    @api.multi
    def compute_invoice_type(self):
        for invoice in self.filtered(lambda i: i.state in ('open', 'paid')):
            categories = invoice.with_context(lang='en_US').mapped(
                'invoice_line_ids.product_id.categ_name')
            if SPONSORSHIP_CATEGORY in categories:
                invoice.invoice_type = 'sponsorship'
            elif GIFT_CATEGORY in categories:
                invoice.invoice_type = 'gift'
            elif FUND_CATEGORY in categories:
                invoice.invoice_type = 'fund'
            else:
                invoice.invoice_type = 'other'

    @api.depends('payment_ids', 'state')
    @api.multi
    def compute_last_payment(self):
        for invoice in self.filtered('payment_ids'):
            filter = 'credit' if invoice.type == 'out_invoice' else 'debit'
            payment_dates = invoice.payment_ids.filtered(filter).mapped(
                'date')
            invoice.last_payment = max(payment_dates or [False])
