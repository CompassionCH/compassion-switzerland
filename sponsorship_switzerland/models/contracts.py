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

import logging
from openerp import api, models, fields, _

logger = logging.getLogger(__name__)


class RecurringContracts(models.Model):
    _inherit = 'recurring.contract'

    first_open_invoice = fields.Date(compute='_compute_first_open_invoice')
    months_paid = fields.Integer(compute='_compute_months_paid')

    @api.multi
    def _compute_first_open_invoice(self):
        for contract in self:
            invoices = contract.invoice_line_ids.mapped('invoice_id').filtered(
                lambda i: i.state == 'open')
            if invoices:
                first_open_invoice = min([
                    fields.Date.from_string(i.date_invoice) for i in invoices])
                contract.first_open_invoice = fields.Date.to_string(
                    first_open_invoice)
            elif contract.state not in ('terminated', 'cancelled'):
                contract.first_open_invoice = contract.next_invoice_date

    @api.multi
    def _compute_months_paid(self):
        """This is a query returning the number of months paid for a
           sponsorship.
        """
        self.env.cr.execute(
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
            "WHERE c.id in (%s)" % ",".join([str(id) for id in self.ids])
        )
        res = self.env.cr.dictfetchall()
        res_map = {row['contract_id']: int(row['paidmonth']) for row in res}
        for contract in self:
            contract.months_paid = res_map[contract.id]

    @api.multi
    def suspend_contract(self):
        """ Launch automatic reconcile after suspension. """
        super(RecurringContracts, self).suspend_contract()
        self._auto_reconcile()
        return True

    @api.multi
    def reactivate_contract(self):
        """ Launch automatic reconcile after reactivation. """
        super(RecurringContracts, self).reactivate_contract()
        self._auto_reconcile()

    @api.onchange('child_id')
    def onchange_child_id(self):
        res = super(RecurringContracts, self).onchange_child_id()
        warn_categories = self.correspondant_id.category_id.filtered(
            'warn_sponsorship')
        if warn_categories:
            cat_names = warn_categories.mapped('name')
            return {
                'warning': {
                    'title': _('The sponsor has special categories'),
                    'message': ', '.join(cat_names)
                }
            }
        return res

    @api.onchange('user_id')
    def onchange_user_id(self):
        """ Make checks as well when ambassador is changed. """
        warn_categories = self.user_id.category_id.filtered(
            'warn_sponsorship')
        if warn_categories:
            cat_names = warn_categories.mapped('name')
            return {
                'warning': {
                    'title': _('The ambassador has special categories'),
                    'message': ', '.join(cat_names)
                }
            }

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_active(self):
        """ Hook for doing something when contract is activated.
        Update partner to add the 'Sponsor' category
        """
        super(RecurringContracts, self).contract_active()
        sponsor_cat_id = self.env.ref(
            'partner_compassion.res_partner_category_sponsor').id
        sponsorships = self.filtered(lambda c: 'S' in c.type)
        add_sponsor_vals = {'category_id': [(4, sponsor_cat_id)]}
        sponsorships.mapped('partner_id').write(add_sponsor_vals)
        sponsorships.mapped('correspondant_id').write(add_sponsor_vals)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _clean_invoices(self, since_date=None, to_date=None, keep_lines=None):
        """ Perform an automatic reconcile after cleaning invoices """
        invoices = super(RecurringContracts, self)._clean_invoices(
            since_date, to_date, keep_lines)
        self._auto_reconcile()
        return invoices

    def _auto_reconcile(self):
        client_account = self.env['account.account'].search([
            ('code', '=', '1050')])
        auto_rec = self.env['account.automatic.reconcile'].create({
            'account_ids': [(4, client_account.id)]
        })
        try:
            auto_rec.reconcile()
        except:
            logger.error("Unable to perform automatic reconciliation after "
                         "cleaning contract invoices.")

    def _filter_clean_invoices(self, since_date, to_date):
        """ For LSV/DD contracts, don't clean invoices that are in a
            Payment Order.
        """
        search = super(RecurringContracts, self)._filter_clean_invoices(
            since_date, to_date)
        invoices = self.env['account.invoice.line'].search(search).mapped(
            'invoice_id')
        lsv_dd_invoices = self._get_lsv_dd_invoices(invoices)

        search.append(('invoice_id', 'not in', lsv_dd_invoices.ids))
        return search

    def _get_invoice_lines_to_clean(self, since_date, to_date):
        """ For LSV/DD contracts, don't clean invoices that are in a
            Payment Order.
        """
        invoice_lines = super(
            RecurringContracts, self)._get_invoice_lines_to_clean(
                since_date, to_date)
        lsv_dd_invoices = self._get_lsv_dd_invoices(invoice_lines.mapped(
            'invoice_id'))
        return invoice_lines.filtered(
            lambda line: line.invoice_id.id not in lsv_dd_invoices.ids)

    def _get_lsv_dd_invoices(self, invoices):
        lsv_dd_invoices = self.env['account.invoice']
        for invoice in invoices:
            pay_line = self.env['payment.line'].search([
                ('move_line_id', 'in', invoice.move_id.line_id.ids),
                ('order_id.state', 'in', ('open', 'done'))])
            if pay_line:
                lsv_dd_invoices += invoice

            # If a draft payment order exitst, we remove the payment line.
            pay_line = self.env['payment.line'].search([
                ('move_line_id', 'in', invoice.move_id.line_id.ids),
                ('order_id.state', '=', 'draft')])
            if pay_line:
                pay_line.unlink()
        return lsv_dd_invoices

    @api.multi
    def _on_sponsorship_finished(self):
        """ Called when a sponsorship is terminated or cancelled:
            Remove sponsor category if sponsor has no other active
            sponsorships.
        """
        super(RecurringContracts, self)._on_sponsorship_finished()
        sponsor_cat_id = self.env.ref(
            'partner_compassion.res_partner_category_sponsor').id
        old_sponsor_cat_id = self.env.ref(
            'partner_compassion.res_partner_category_old').id

        for sponsorship in self:
            partner_id = sponsorship.partner_id.id
            correspondant_id = sponsorship.correspondant_id.id
            # Partner
            contract_count = self.search_count([
                '|',
                ('correspondant_id', '=', partner_id),
                ('partner_id', '=', partner_id),
                ('state', '=', 'active'),
                ('type', 'like', 'S')])
            if not contract_count:
                # Replace sponsor category by old sponsor category
                sponsorship.partner_id.write({
                    'category_id': [(3, sponsor_cat_id),
                                    (4, old_sponsor_cat_id)]})
            # Correspondant
            contract_count = self.search_count([
                '|',
                ('correspondant_id', '=', correspondant_id),
                ('partner_id', '=', correspondant_id),
                ('state', '=', 'active'),
                ('type', 'like', 'S')])
            if not contract_count:
                # Replace sponsor category by old sponsor category
                sponsorship.correspondant_id.write({
                    'category_id': [(3, sponsor_cat_id),
                                    (4, old_sponsor_cat_id)]})
