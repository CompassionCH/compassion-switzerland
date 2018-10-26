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
from odoo import models, fields

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    registration_id = fields.Many2one('event.registration', 'Registration')

    def _get_payment_invoice_vals(self):
        vals = super(PaymentTransaction, self)._get_payment_invoice_vals()
        vals['transaction_id'] = self.postfinance_payid
        return vals

    def _get_auto_post_invoice(self):
        if 'EVENT-DON' in self.reference:
            # Only post when partner was not created
            return self.partner_id.state == 'active'
        return super(PaymentTransaction, self)._get_auto_post_invoice()
