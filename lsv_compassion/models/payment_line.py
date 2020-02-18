##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, fields


class PaymentLine(models.Model):
    _inherit = "account.payment.line"

    invoice_type = fields.Selection(related="move_line_id.invoice_id.invoice_type")


class BankPaymentLine(models.Model):
    _inherit = "bank.payment.line"

    invoice_type = fields.Selection(related="payment_line_ids.invoice_type")

    @api.model
    def same_fields_payment_line_and_bank_payment_line(self):
        """
        Group payment lines by invoice type.
        :return: list of grouping fields
        """
        res = super().same_fields_payment_line_and_bank_payment_line()
        res.append("invoice_type")
        return res
