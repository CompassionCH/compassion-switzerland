# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def pay_muskathlon_invoice(self):
        """
        Make a payment to reconcile Muskathlon invoice.
        :return: True
        """
        if self.state == 'paid':
            return True
        muskathlon_user = self.env.ref('muskathlon.user_muskathlon_portal')
        payment_vals = {
            'journal_id': self.env['account.journal'].search(
                [('name', '=', 'Web')]).id,
            'payment_method_id': self.env['account.payment.method'].search(
                [('code', '=', 'sepa_direct_debit')]).id,
            'payment_date': fields.Date.today(),
            'communication': self.reference,
            'invoice_ids': [(6, 0, self.ids)],
            'payment_type': 'inbound',
            'amount': self.amount_total,
            'currency_id': self.currency_id.id,
            'partner_id': self.partner_id.id,
            'partner_type': 'customer',
            'payment_difference_handling': 'reconcile',
            'payment_difference': self.amount_total,
        }
        account_payment = self.env['account.payment'].create(payment_vals)
        if self.partner_id.write_uid != muskathlon_user:
            # Validate self and post the payment.
            if self.state == 'draft':
                self.action_invoice_open()
            account_payment.post()
        return True
