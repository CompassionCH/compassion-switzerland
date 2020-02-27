##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_auto_post_invoice(self):
        if 'MUSK-REG' in self.reference:
            # Only post when partner was not created
            return self.partner_id.state == 'active'
        return super(PaymentTransaction, self)._get_auto_post_invoice()
