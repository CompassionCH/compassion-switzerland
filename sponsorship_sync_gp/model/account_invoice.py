# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp.osv import orm, fields
from openerp.tools.translate import _

from . import gp_connector
from .contracts import SPONSORSHIP_TYPES


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    # Add a field to know if we sent the receipt for a paid invoice
    _columns = {
        'receipt_id': fields.many2one('mail.message', _('Receipt'))
    }

    def action_cancel(self, cr, uid, ids, context=None):
        """ If an invoice was cancelled, update the situation in GP. """
        for invoice in self.browse(cr, uid, ids, {'lang': 'en_US'}):
            # Customer invoice going from 'open' to 'cancel' state
            if invoice.type == 'out_invoice' and invoice.state == 'open':
                contract_ids = set()
                gp_connect = gp_connector.GPConnect()
                for line in invoice.invoice_line:
                    contract = line.contract_id
                    if contract and contract.id not in contract_ids \
                            and line.product_id.name in SPONSORSHIP_TYPES:
                        contract_ids.add(contract.id)
                        # Removes one month due in GP.
                        if not gp_connect.register_payment(
                                contract.id, contract.months_paid+1):
                            raise orm.except_orm(
                                _("GP Sync Error"),
                                _("The cancellation could not be registered "
                                  "into GP. Please contact an IT person."))
        return super(account_invoice, self).action_cancel(cr, uid, ids,
                                                          context)

    def action_move_create(self, cr, uid, ids, context=None):
        """ If an invoice was cancelled,
            and validated again, update the situation in GP.
        """
        res = super(account_invoice, self).action_move_create(cr, uid, ids,
                                                              context)
        for invoice in self.browse(cr, uid, ids, {'lang': 'en_US'}):
            if invoice.type == 'out_invoice' and invoice.internal_number:
                contract_ids = set()
                gp_connect = gp_connector.GPConnect()
                for line in invoice.invoice_line:
                    contract = line.contract_id
                    if contract and contract.id not in contract_ids \
                            and line.product_id.name in SPONSORSHIP_TYPES:
                        contract_ids.add(contract.id)
                        if not gp_connect.undo_payment(contract.id):
                            raise orm.except_orm(
                                _("GP Sync Error"),
                                _("Please contact an IT person."))
        return res

    def get_funds_paid(self, cr, uid, from_date, to_date, context=None):
        """ Search invoices paid in the given period which are not
            sponsorships and return the ids. """
        invl_obj = self.pool.get('account.invoice.line')
        invl_ids = invl_obj.search(
            cr, uid, [
                ('state', '=', 'paid'),
                ('last_payment', '>=', from_date),
                ('last_payment', '<=', to_date),
                ('contract_id', '=', False),
                ('price_subtotal', '>', 8),
                ('product_id.name', '!=', 'The 4th Musketeer Fund')],
            context=context)

        return list(set([invl.invoice_id.id for invl in
                         invl_obj.browse(cr, uid, invl_ids, context)]))
