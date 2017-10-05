# -*- coding: utf-8 -*-
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
from datetime import datetime

from dateutil.relativedelta import relativedelta
from odoo.tools import mod10r

from odoo import api, models, fields, _

logger = logging.getLogger(__name__)


class RecurringContracts(models.Model):
    _inherit = 'recurring.contract'

    first_open_invoice = fields.Date(compute='_compute_first_open_invoice')
    has_mandate = fields.Boolean(compute='_compute_has_mandate')
    contract_line_ids = fields.One2many(
        default=lambda self: self._get_standard_lines()
    )

    @api.model
    def _get_states(self):
        """ Add a waiting mandate state """
        states = super(RecurringContracts, self)._get_states()
        states.insert(2, ('mandate', _('Waiting Mandate')))
        return states

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
    def _compute_has_mandate(self):
        # Search for an existing valid mandate
        for contract in self:
            count = self.env['account.banking.mandate'].search_count([
                ('partner_id', '=', contract.partner_id.id),
                ('state', '=', 'valid')])
            contract.has_mandate = bool(count)

    @api.model
    def _get_sponsorship_standard_lines(self):
        """ Select Sponsorship and General Fund by default """
        res = []
        product_obj = self.env['product.product'].with_context(lang='en_US')
        sponsorship_id = product_obj.search(
            [('name', '=', 'Sponsorship')])[0].id
        gen_id = product_obj.search(
            [('name', '=', 'General Fund')])[0].id
        sponsorship_vals = {
            'product_id': sponsorship_id,
            'quantity': 1,
            'amount': 42,
            'subtotal': 42
        }
        gen_vals = {
            'product_id': gen_id,
            'quantity': 1,
            'amount': 8,
            'subtotal': 8
        }
        res.append([0, 6, sponsorship_vals])
        res.append([0, 6, gen_vals])
        return res

    @api.model
    def _get_standard_lines(self):
        if 'S' in self.env.context.get('default_type', 'O'):
            return self._get_sponsorship_standard_lines()
        return []

    @api.multi
    def write(self, vals):
        """ Perform various checks when a contract is modified. """
        if 'group_id' in vals:
            self._on_change_group_id(vals['group_id'])

        # Write the changes
        return super(RecurringContracts, self).write(vals)

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

    @api.onchange('group_id')
    def on_change_group_id(self):
        """ Compute next invoice_date """
        current_date = datetime.today()
        is_active = False

        if self.state not in ('draft',
                              'mandate') and self.next_invoice_date:
            is_active = True
            current_date = fields.Datetime.from_string(
                self.next_invoice_date)

        if self.group_id:
            contract_group = self.group_id
            if contract_group.next_invoice_date:
                next_group_date = fields.Datetime.from_string(
                    contract_group.next_invoice_date)
                next_invoice_date = current_date.replace(
                    day=next_group_date.day)
            else:
                next_invoice_date = current_date.replace(day=1)
            payment_mode = contract_group.payment_mode_id.name
        else:
            next_invoice_date = current_date.replace(day=1)
            payment_mode = ''

        if current_date.day > 15 or (payment_mode in (
                'LSV', 'Postfinance') and not is_active):
            next_invoice_date += relativedelta(months=+1)
        self.next_invoice_date = fields.Date.to_string(next_invoice_date)

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
        sponsorships.mapped('partner_id').update_church_sponsorships_number(
            True)
        sponsorships.mapped(
            'correspondant_id').update_church_sponsorships_number(
            True)
        return True

    @api.multi
    def contract_waiting_mandate(self):
        self.write({'state': 'mandate'})
        return super(RecurringContracts, self).contract_waiting_mandate()

    @api.multi
    def contract_waiting(self):
        vals = {'state': 'waiting'}
        for contract in self:
            payment_mode = contract.payment_mode_id.name
            if contract.type == 'S' and ('LSV' in payment_mode or
                                         'Postfinance' in payment_mode):
                # Recompute next_invoice_date
                today = datetime.today()
                old_invoice_date = fields.Datetime.from_string(
                    contract.next_invoice_date)
                next_invoice_date = old_invoice_date.replace(
                    month=today.month, year=today.year)
                if today.day > 15 and next_invoice_date.day < 15:
                    next_invoice_date = next_invoice_date + relativedelta(
                        months=+1)
                if next_invoice_date > old_invoice_date:
                    vals['next_invoice_date'] = \
                        fields.Date.to_string(next_invoice_date)

            contract.write(vals)
        return super(RecurringContracts, self).contract_waiting()

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
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
            pay_line = self.env['account.payment.line'].search([
                ('move_line_id', 'in', invoice.move_id.line_ids.ids),
                ('order_id.state', 'in', ('open', 'done'))])
            if pay_line:
                lsv_dd_invoices += invoice

            # If a draft payment order exitst, we remove the payment line.
            pay_line = self.env['account.payment.line'].search([
                ('move_line_id', 'in', invoice.move_id.line_ids.ids),
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

            sponsorship.partner_id.update_church_sponsorships_number(False)
            sponsorship.correspondant_id.update_church_sponsorships_number(
                False)

    def _on_change_group_id(self, group_id):
        """ Change state of contract if payment is changed to/from LSV or DD.
        """
        group = self.env['recurring.contract.group'].browse(
            group_id)
        payment_name = group.payment_mode_id.name
        if group and ('LSV' in payment_name or 'Postfinance' in payment_name):
            self.signal_workflow('will_pay_by_lsv_dd')
        else:
            # Check if old payment_mode was LSV or DD
            for contract in self.filtered('group_id'):
                payment_name = contract.payment_mode_id.name
                if 'LSV' in payment_name or 'Postfinance' in payment_name:
                    contract.signal_workflow('mandate_validated')

    @api.multi
    def _update_invoice_lines(self, invoices):
        """ Update bvr_reference of invoices """
        super(RecurringContracts, self)._update_invoice_lines(invoices)
        for contract in self:
            ref = False
            bank_modes = self.env['account.payment.mode'].with_context(
                lang='en_US').search(
                ['|', ('name', 'like', 'LSV'),
                 ('name', 'like', 'Postfinance')])
            if contract.group_id.bvr_reference:
                ref = contract.group_id.bvr_reference
            elif contract.payment_mode_id in bank_modes:
                seq = self.env['ir.sequence']
                ref = mod10r(seq.next_by_code('contract.bvr.ref'))
            invoices.write({'reference': ref})
