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

from openerp import models, _


class payment_order(models.Model):
    _inherit = "payment.order"

    def action_open(self):
        """ Logs a note in invoices when imported in payment order """
        for order in self:
            for line in order.line_ids:
                self.env['mail.thread'].message_post(
                    line.ml_inv_ref.id,
                    _("The invoice has been imported in a payment order."),
                    _("Invoice Collected for LSV/DD"), 'comment')

        return super(payment_order, self).action_open()

    def action_cancel(self):
        """ Logs a note in invoices when order is cancelled. """
        self.write({'state': 'cancel'})
        for order in self:
            for line in order.line_ids:
                self.env['mail.thread'].message_post(
                    line.ml_inv_ref.id,
                    _("The LSV/DD Order has been cancelled."),
                    _("Payment Order Cancelled"), 'comment')

        return True
