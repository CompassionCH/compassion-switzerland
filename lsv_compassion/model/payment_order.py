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
            for line in order.line_ids:
                line.ml_inv_ref.message_post(
                    _("The invoice has been imported in a payment order."),
                    _("Invoice Collected for LSV/DD"), 'comment')

        return super(payment_order, self).action_open()

    @api.multi
    def action_cancel(self):
        """ Logs a note in invoices when order is cancelled. """
        self.write({'state': 'cancel'})
        for order in self:
            for line in order.line_ids:
                line.ml_inv_ref.message_post(
                    _("The LSV/DD Order has been cancelled."),
                    _("Payment Order Cancelled"), 'comment')

        return True
