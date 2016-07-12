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
from openerp import api, models, _

logger = logging.getLogger(__name__)


class contracts(models.Model):
    _inherit = 'recurring.contract'

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _get_gmc_states(self):
        """ Adds a new gmc state for tracking sponsorships for which we have
        to order the new picture of the child. Remove 'casestudy' and
        'picture' states which are useless for Switzerland."""
        return [
            ('order_picture', _('Order Picture')),
            ('biennial', _('Biennial')),
            ('depart', _('Child Departed')),
            ('transfer', _('Child Transfer'))]

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def new_biennial(self):
        """ Called when new picture and new case study is available. """
        self.write({'gmc_state': 'order_picture'})

    @api.multi
    def set_gmc_event(self, event):
        """
        Called when a Child Update was received for a sponsored child.
        Arg event can have one of the following values :
            - Transfer : child was transferred to another project
            - CaseStudy : child has a new casestudy
            - NewImage : child has a new image

        We handle only the Transfer event, as other events are not relevant
        for Switzerland.
        """
        if event == 'Transfer':
            return self.write({'gmc_state': event.lower()})
        return True

    @api.multi
    def suspend_contract(self):
        """ Launch automatic reconcile after suspension. """
        super(contracts, self).suspend_contract()
        self._auto_reconcile()
        return True

    @api.multi
    def reactivate_contract(self):
        """ Launch automatic reconcile after reactivation. """
        super(contracts, self).reactivate_contract()
        self._auto_reconcile()

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.model
    def button_reset_gmc_state(self, value):
        """ Button called from Kanban view on all contracts of one group. """

        contracts = self.env['recurring.contract'].search([
            ('gmc_state', '=', value)])
        return contracts.reset_gmc_state()

    @api.multi
    def reset_gmc_state(self):
        """ Useful for manually unset GMC State. """
        return self.write({'gmc_state': False})

    # Called only at module installation
    @api.model
    def migrate_contracts(self):
        """ Remove no more used gmc_states. """
        self.env.cr.execute("""
            UPDATE recurring_contract SET gmc_state = NULL
            WHERE gmc_state IN ('picture', 'casestudy')
        """)
        self.env.invalidate_all()
        return True

    ##########################################################################
    #                            WORKFLOW METHODS                            #
    ##########################################################################
    @api.multi
    def contract_active(self):
        """ Hook for doing something when contract is activated.
        Update partner to add the 'Sponsor' category
        """
        super(contracts, self).contract_active()
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
        invoices = super(contracts, self)._clean_invoices(
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

    def _filter_clean_invoices(self, since_date=None, to_date=None,
                               gifts=False):
        """ For LSV/DD contracts, don't clean invoices that are in a
            Payment Order.
        """
        search = super(contracts, self)._filter_clean_invoices(
            since_date, to_date, gifts)
        invoices = self.env['account.invoice.line'].search(search).mapped(
            'invoice_id')
        lsv_dd_invoices = self._get_lsv_dd_invoices(invoices)

        search.append(('invoice_id', 'not in', lsv_dd_invoices.ids))
        return search

    def _get_invoice_lines_to_clean(self, since_date, to_date):
        """ For LSV/DD contracts, don't clean invoices that are in a
            Payment Order.
        """
        invoice_lines = super(contracts, self)._get_invoice_lines_to_clean(
            since_date, to_date)
        lsv_dd_invoices = self._get_lsv_dd_invoices(invoice_lines.mapped(
            'invoice_id'))
        return invoice_lines.filtered(
            lambda line: line.invoice_id not in lsv_dd_invoices.ids)

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
        super(contracts, self)._on_sponsorship_finished()
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
