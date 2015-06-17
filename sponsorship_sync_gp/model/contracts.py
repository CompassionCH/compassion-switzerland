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
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT as DF

from datetime import datetime
from dateutil.relativedelta import relativedelta

from . import gp_connector


class contracts(orm.Model):
    _inherit = 'recurring.contract'

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    def _get_number_months_paid(self, cr, uid, ids, field_name, args,
                                context=None):
        """This is a query returning the number of months paid for a
        sponsorship. It is useful to know it in GP."""
        cr.execute(
            "SELECT c.id as contract_id, "
            "12 * (EXTRACT(year FROM next_invoice_date) - "
            "      EXTRACT(year FROM current_date))"
            " + EXTRACT(month FROM c.next_invoice_date) - 1"
            " - COALESCE(due.total, 0) as paidmonth "
            "FROM recurring_contract c left join ("
            # Open invoices to find how many months are due
            "   select contract_id, count(distinct invoice_id) as total "
            "   from account_invoice_line l join product_product p on "
            "       l.product_id = p.id "
            "   where state='open' and "
            # Exclude gifts from count
            "   categ_name != 'Sponsor gifts'"
            "   group by contract_id"
            ") due on due.contract_id = c.id "
            "WHERE c.id in (%s)" % ",".join([str(id) for id in ids])
        )
        res = cr.dictfetchall()
        return {row['contract_id']: int(row['paidmonth']) for row in res}

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    _columns = {
        'months_paid': fields.function(_get_number_months_paid,
                                       type='integer', string='Months paid'),
    }

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    def create(self, cr, uid, vals, context=None):
        """ When contract is created, push it to GP so that the mailing
        module can access all information. """
        contract_id = super(contracts, self).create(cr, uid, vals, context)
        gp_connect = gp_connector.GPConnect()
        # Read data in english
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        # Write contract in GP
        contract = self.browse(cr, uid, contract_id, ctx)
        self._write_contract_in_gp(uid, gp_connect, contract)

        return contract_id

    def write(self, cr, uid, ids, vals, context=None):
        """ Keep GP updated when a contract is modified. """
        # Read data in english
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['lang'] = 'en_US'
        # Do nothing during the invoice generation process
        if context.get('invoice_generation'):
            return super(contracts, self).write(cr, uid, ids, vals, context)

        ids = [ids] if not isinstance(ids, list) else ids
        gp_connect = gp_connector.GPConnect()
        # If we change the next invoice date, it means we cancel
        # invoices generation and should thus update the situation
        # in GP (advance the months paid).
        if vals.get('next_invoice_date'):
            new_date = datetime.strptime(vals['next_invoice_date'], DF)
            for contract in self.browse(cr, uid, ids, context=ctx):
                if 'S' in contract.type:
                    old_date = datetime.strptime(contract.next_invoice_date,
                                                 DF)
                    month_diff = relativedelta(new_date, old_date).months
                    if contract.state in ('active', 'waiting') and \
                            month_diff > 0:
                        if not gp_connect.register_payment(
                                contract.id,
                                contract.months_paid + month_diff):
                            raise orm.except_orm(
                                _("GP Sync Error"),
                                _("Please contact an IT person."))

        # Update GP
        res = super(contracts, self).write(cr, uid, ids, vals, context)
        for contract in self.browse(cr, uid, ids, ctx):
            self._write_contract_in_gp(uid, gp_connect, contract)
        return res

    def unlink(self, cr, uid, ids, context=None):
        super(contracts, self).unlink(cr, uid, ids, context)
        if not isinstance(ids, list):
            ids = [ids]
        gp_connect = gp_connector.GPConnect()
        gp_connect.delete_contracts(ids)
        return True

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def get_month_paid_from_gp(self, cr, uid, con_id, context=None):
        """Helper called from GP"""
        return self.browse(cr, uid, con_id, context).months_paid

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    def contract_waiting(self, cr, uid, ids, context=None):
        """ When contract is validated, calculate which month is due
        and push it to GP.
        """
        super(contracts, self).contract_waiting(cr, uid, ids, context)
        gp_connect = gp_connector.GPConnect()
        for contract in self.browse(cr, uid, ids, context):
            if 'S' in contract.type:
                if not gp_connect.validate_contract(contract):
                    raise orm.except_orm(
                        _("GP Sync Error"),
                        _("The sponsorship could not be validated.") +
                        _("Please contact an IT person."))
        return True

    def action_sds_active(self, cr, uid, ids, context=None):
        """ Log a note in GP when welcome is sent and SDS is state becomes
        active. """
        gp_connect = gp_connector.GPConnect()
        for contract in self.browse(cr, uid, ids, context):
            gp_connect.log_welcome_sent(contract)
        return self.write(cr, uid, ids, {
            'sds_state': 'active', 'color': 0}, context)

    def contract_cancelled(self, cr, uid, ids, context=None):
        """ When contract is cancelled, update it in GP. """
        self._finish_contract(cr, uid, ids, 'cancel', context)
        return True

    def contract_terminated(self, cr, uid, ids, context=None):
        """ When contract is terminated, update it in GP. """
        self._finish_contract(cr, uid, ids, 'terminate', context)
        return True

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _finish_contract(self, cr, uid, ids, finish_type, context=None):
        """ Avoid useless syncs of Affectats when a contract is terminated.
        """
        if context is None:
            context = dict()
        ctx = context.copy()
        ctx['skip_invoice_sync'] = True

        if finish_type == 'cancel':
            super(contracts, self).contract_cancelled(cr, uid, ids, ctx)
        elif finish_type == 'terminate':
            super(contracts, self).contract_terminated(cr, uid, ids, ctx)

    def _on_sponsorship_finished(self, cr, uid, ids, context=None):
        """ When contract is finished, update it in GP. """
        gp_connect = gp_connector.GPConnect()
        for contract in self.browse(cr, uid, ids, context):
            if not gp_connect.finish_contract(uid, contract):
                raise orm.except_orm(
                    _("GP Sync Error"),
                    _("The sponsorship could not be terminated.") +
                    _("Please contact an IT person."))

    def _write_contract_in_gp(self, uid, gp_connect, contract):
        if self._is_gp_compatible(contract):
            if not gp_connect.upsert_contract(uid, contract):
                raise orm.except_orm(
                    _("GP Sync Error"),
                    _("Please contact an IT person."))
        elif 'S' in contract.type:
            raise orm.except_orm(
                _("Not compatible with GP"),
                _("You selected some products that are not available "
                  "in GP.") + _("You cannot save this contract."))

    def _is_gp_compatible(self, contract):
        """ Tells if the contract is compatible with GP. """
        compatible = 'S' in contract.type
        if compatible:
            for line in contract.contract_line_ids:
                compatible = compatible and (
                    line.product_id.categ_name == 'Sponsorship' or
                    line.product_id.gp_fund_id > 0)
        return compatible

    def _on_contract_active(self, cr, uid, ids, context=None):
        """ When contract is active, update it in GP. """
        super(contracts, self)._on_contract_active(cr, uid, ids, context)
        gp_connect = gp_connector.GPConnect()
        for contract in self.browse(cr, uid, ids, context):
            if 'S' in contract.type:
                if not gp_connect.activate_contract(contract):
                    raise orm.except_orm(
                        _("GP Sync Error"),
                        _("The sponsorship could not be activated.") +
                        _("Please contact an IT person."))
                # Update the months paid in GP
                gp_connect.register_payment(contract.id, contract.months_paid)

    def _invoice_paid(self, cr, uid, invoice, context=None):
        """ When a customer invoice is paid, synchronize GP. """
        super(contracts, self)._invoice_paid(cr, uid, invoice, context)
        if invoice.payment_ids:
            # Retrieve the id of the person which reconciled the invoice
            uid = invoice.payment_ids[0].reconcile_id.perm_read()[0][
                'create_uid'][0]
        if invoice.type == 'out_invoice' and not \
                context.get('skip_invoice_sync'):
            gp_connect = gp_connector.GPConnect()
            last_pay_date = max([move_line.date
                                 for move_line in invoice.payment_ids
                                 if move_line.credit > 0] or [False])
            contract_ids = set()
            for line in invoice.invoice_line:
                if last_pay_date:
                    gp_connect.insert_affectat(uid, line, last_pay_date)
                else:   # Invoice will go back in open state
                    gp_connect.remove_affectat(line.id)
                contract = line.contract_id
                if contract and 'S' in contract.type:
                    to_update = (line.product_id.categ_name ==
                                 'Sponsorship') and (contract.id
                                                     not in contract_ids)
                    if last_pay_date and to_update:
                        contract_ids.add(contract.id)
                        # Set the months_paid to months_paid+1, as the new
                        # paid invoice is not yet counted.
                        if not gp_connect.register_payment(
                                contract.id, contract.months_paid+1,
                                last_pay_date):
                            raise orm.except_orm(
                                _("GP Sync Error"),
                                _("The payment could not be registered into "
                                  "GP.") + _("Please contact an IT person."))
                    elif to_update:
                        contract_ids.add(contract.id)
                        if not gp_connect.undo_payment(contract.id):
                            raise orm.except_orm(
                                _("GP Sync Error"),
                                _("The payment could not be removed "
                                  "from GP.") + _("Please contact an IT "
                                                  "person."))

    def _on_invoice_line_removal(self, cr, uid, invoice_lines, context=None):
        """ Removes the corresponding Affectats in GP.
            @param: invoice_lines (dict): {
                line_id: [invoice_id, child_code, product_name, amount]}
        """
        super(contracts, self)._on_invoice_line_removal(
            cr, uid, invoice_lines, context)
        if not context.get('skip_invoice_sync'):
            gp_connect = gp_connector.GPConnect()
            for line_id in invoice_lines.keys():
                gp_connect.remove_affectat(line_id)


class contract_group(orm.Model):
    """ Update all contracts when group is changed. """
    _inherit = 'recurring.contract.group'

    def write(self, cr, uid, ids, vals, context=None):
        res = super(contract_group, self).write(cr, uid, ids, vals, context)
        gp_connect = gp_connector.GPConnect()
        for group in self.browse(cr, uid, ids, context):
            for contract in group.contract_ids:
                if 'S' in contract.type:
                    if not gp_connect.upsert_contract(uid, contract):
                        raise orm.except_orm(
                            _("GP Sync Error"),
                            _("Please contact an IT person."))
        return res

    def _generate_invoice_lines(self, cr, uid, contract, invoice_id,
                                context=None):
        """Add in context the information that the generation process is
        working so that GP is not updated during it."""
        if context is None:
            context = {}
        ctx = context.copy()
        ctx['invoice_generation'] = True
        ctx['lang'] = 'en_US'   # Generate everything in english
        super(contract_group, self)._generate_invoice_lines(
            cr, uid, contract, invoice_id, ctx)
