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

from openerp.osv import orm
from openerp.tools.translate import _


class payment_order(orm.Model):
    _inherit = "payment.order"

    def action_open(self, cr, uid, ids, context=None):
        """ Logs a note in invoices when imported in payment order """
        for order in self.browse(cr, uid, ids, context):
            for line in order.line_ids:
                self.pool.get('mail.thread').message_post(
                    cr, uid, line.ml_inv_ref.id,
                    _("The invoice has been imported in a payment order."),
                    _("Invoice Collected for LSV/DD"), 'comment',
                    context={'thread_model': 'account.invoice'})

        return super(payment_order, self).action_open(cr, uid, ids, context)

    def action_cancel(self, cr, uid, ids, context=None):
        """ Logs a note in invoices when order is cancelled. """
        self.write(cr, uid, ids, {'state': 'cancel'}, context)
        for order in self.browse(cr, uid, ids, context):
            for line in order.line_ids:
                self.pool.get('mail.thread').message_post(
                    cr, uid, line.ml_inv_ref.id,
                    _("The LSV/DD Order has been cancelled."),
                    _("Payment Order Cancelled"), 'comment',
                    context={'thread_model': 'account.invoice'})

        return True
