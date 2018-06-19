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
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import models, api, fields
from odoo.addons.queue_job.job import job, related_action


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    @job(default_channel='root.muskathlon')
    @related_action('related_action_invoice')
    def pay_muskathlon_invoice(self):
        """Make a payment to reconcile Muskathlon invoice."""
        if self.state == 'paid':
            return True
        muskathlon_user = self.env.ref('muskathlon.user_muskathlon_portal')
        # Look for existing payment
        payment = self.env['account.payment'].search([
            ('invoice_ids', '=', self.id)
        ])
        if payment:
            return True
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
        limit_date = date.today() - relativedelta(days=3)
        create_date = fields.Date.from_string(self.partner_id.create_date)
        if self.partner_id.create_uid != muskathlon_user and \
                create_date < limit_date:
            # Validate self and post the payment.
            if self.state == 'draft':
                self.action_invoice_open()
            account_payment.post()
        return True

    @api.multi
    @job(default_channel='root.muskathlon')
    def delete_muskathlon_invoice(self):
        """Cancel Muskathlon invoice"""
        return self.unlink()
