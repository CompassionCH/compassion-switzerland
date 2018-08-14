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
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import models, fields

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    registration_id = fields.Many2one(
        'muskathlon.registration', 'Registration')

    def _get_payment_invoice_vals(self):
        vals = super(PaymentTransaction, self)._get_payment_invoice_vals()
        vals['transaction_id'] = self.postfinance_payid
        return vals

    def _get_auto_post_invoice(self):
        if 'MUSK' in self.reference:
            # Only post when partner was not created
            limit_date = date.today() - relativedelta(days=3)
            create_date = fields.Date.from_string(self.partner_id.create_date)
            muskathlon_user = self.env.ref('muskathlon.user_muskathlon_portal')
            return self.partner_id.create_uid != muskathlon_user and \
                create_date < limit_date
        return super(PaymentTransaction, self)._get_auto_post_invoice()
