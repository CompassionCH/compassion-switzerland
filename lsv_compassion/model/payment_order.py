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

from openerp import models, api, _


class payment_order(models.Model):
    _inherit = "payment.order"

    @api.multi
    def action_open(self):
        """ Logs a note in invoices when imported in payment order """
        for order in self:
            order_type = order._get_order_type()
            if order_type:
                for invoice in order.mapped('line_ids.ml_inv_ref'):
                    invoice.message_post(
                        _("The invoice has been imported in a payment "
                          "order."),
                        _("Invoice Collected for ") + order_type, 'comment')

        return super(payment_order, self).action_open()

    @api.multi
    def action_cancel(self):
        """ Logs a note in invoices when order is cancelled. """
        self.write({'state': 'cancel'})
        for order in self:
            order_type = order._get_order_type()
            if order_type:
                for invoice in order.mapped('line_ids.ml_inv_ref'):
                    invoice.message_post(
                        _("The %s Order has been cancelled.") % order_type,
                        _("Payment Order Cancelled"), 'comment')

        return True

    def _get_order_type(self):
        """ Tells if payment term is LSV or DD and returns the name. """
        payment_term_lsv_dd = False
        payment_term_names = self.mode.mapped('payment_term_ids.name')
        for payment_name in payment_term_names:
            if 'LSV' in payment_name:
                payment_term_lsv_dd = 'LSV'
            elif 'Postfinance' in payment_name:
                payment_term_lsv_dd = 'DD'
        return payment_term_lsv_dd
