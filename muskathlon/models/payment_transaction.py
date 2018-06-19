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

    registration_id = fields.Many2one(
        'muskathlon.registration', 'Registration')
    invoice_id = fields.Many2one(
        'account.invoice', 'Donation')

    @api.multi
    def cancel_transaction(self):
        """
        Called by ir_action_rule in order to cancel the transaction that
        was not updated after a while.
        :return: True
        """
        self.invoice_id.unlink()
        self.registration_id.unlink()
        return self.write({
            'state': 'cancel',
            'state_message': 'No update of the transaction within 10 minutes.'
        })

    @api.multi
    def cancel_transaction_on_update(self):
        """
        Called by ir_action_rule in when transaction was cancelled by user.
        :return: True
        """
        self.invoice_id.unlink()
        self.registration_id.unlink()
        return True

    @api.multi
    def confirm_transaction(self):
        """
        Called by ir_action_rule when transaction is done.
        :return: True
        """
        # Avoids launching several times the same job. Since there are 3
        # calls to the write method of payment.transaction during a transaction
        # feedback, this action_rule is triggered 3 times. We want to avoid it.
        queue_job = self.env['queue.job'].search([
            ('channel', '=', 'root.muskathlon'),
            ('state', '!=', 'done'),
            ('func_string', 'like', str(self.ids)),
            ('name', 'ilike', 'reconcile Muskathlon invoice')
        ])
        if not queue_job:
            self.invoice_id.with_delay().pay_muskathlon_invoice({
                'transaction_id': self.postfinance_payid,
                'payment_mode_id': self.payment_mode_id.id
            })
