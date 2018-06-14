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
    def confirm_transaction(self):
        """
        Called by ir_action_rule in order to confirm the transaction that
        was not updated after a while.
        :return: True
        """
        self.invoice_id.pay_muskathlon_invoice()
