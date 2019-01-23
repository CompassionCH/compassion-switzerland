# coding: utf-8
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    registration_id = fields.Many2one('event.registration', 'Registration')

    @api.multi
    def cancel_transaction(self):
        """
        Called by ir_action_rule in order to cancel the transaction that
        was not updated after a while.
        => Cancel donation invoices
        :return: True
        """
        for transaction in self:
            if 'EVENT-DON' in transaction.reference:
                transaction.invoice_id.action_invoice_cancel()
        return super(PaymentTransaction, self).cancel_transaction()

    @api.multi
    def cancel_transaction_on_update(self):
        """
        Called by ir_action_rule in when transaction was cancelled by user.
        => Cancel donation invoices
        :return: True
        """
        for transaction in self:
            if 'EVENT-DON' in transaction.reference:
                transaction.invoice_id.action_invoice_cancel()
        return super(PaymentTransaction, self).cancel_transaction_on_update()

    def _get_payment_invoice_vals(self):
        vals = super(PaymentTransaction, self)._get_payment_invoice_vals()
        vals['transaction_id'] = self.postfinance_payid
        return vals

    def _get_auto_post_invoice(self):
        if 'EVENT-DON' in self.reference:
            # Only post when partner was not created
            return self.partner_id.state == 'active'
        return super(PaymentTransaction, self)._get_auto_post_invoice()
