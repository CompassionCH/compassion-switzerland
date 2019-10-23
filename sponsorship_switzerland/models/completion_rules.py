# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import re
from odoo import models, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.addons.sponsorship_compassion.models.product import \
    GIFT_CATEGORY, GIFT_REF

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StatementCompletionRule(models.Model):
    """ Rules to complete account bank statements."""
    _inherit = "account.statement.completion.rule"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################

    sequence = fields.Integer('Sequence',
                              help="Lower means parsed first.")
    name = fields.Char('Name', size=128)
    journal_ids = fields.Many2many(
        'account.journal',
        string='Related statement journal')
    function_to_call = fields.Selection('_get_functions', 'Method')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################

    def _get_functions(self):
        res = super(StatementCompletionRule, self)._get_functions()
        res.extend([
            ('get_from_partner_ref',
             'Compassion: From line reference '
             '(based on the partner reference)'),
            ('get_from_bvr_ref',
             'Compassion: From line reference '
             '(based on the BVR reference of the sponsor)'),
            ('lsv_dd_get_from_bvr_ref',
             'Compassion [LSV/DD]: From line reference '
             '(based on the BVR reference of the sponsor)'),
            ('get_from_lsv_dd', 'Compassion: Put LSV DD Credits in 1098'),
            ('get_sponsor_name',
             'Compassion[POST]: From sponsor reference '
             '(based the sponsor name in the description)'),
        ])
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################

    def get_from_partner_ref(self, stmts_vals, st_line):
        """
        If line ref match a partner reference, update partner and account
        Then, call the generic st_line method to complete other values.
        :param dict st_line: read of the concerned account.bank.statement.line
        :return:
            A dict of value that can be passed directly to the write method of
            the statement line or {}
           {'partner_id': value,
            'account_id' : value,
            ...}
        """
        ref = ''
        if 'ref' in st_line:
            ref = st_line['ref']
        res = {}

        ref_index = 9  # position of the partner ref inside the BVR number.
        partner_ref = ref[ref_index:16]
        partner_obj = self.env['res.partner']
        partner = partner_obj.search([('ref', '=', str(int(partner_ref)))])
        if not partner:
            # Some bvr reference have a wrong number of leading zeros,
            # resulting in the partner reference to be offset.
            flexible_ref_match = re.search(r'^0{,10}([1-9]\d{4,6})0',
                                           ref)
            if flexible_ref_match:
                flexible_ref = flexible_ref_match.group(1)
                if int(flexible_ref) != int(partner_ref):
                    logger.warning(
                        'The partner reference might be misaligned: %s',
                        ref)
                    partner = partner_obj.search([
                        ('ref', '=', str(int(flexible_ref)))])
                    ref_index = flexible_ref_match.start(1)
        if len(partner) > 1:
            # Take only those who have active sponsorships
            partner = partner.filtered(lambda p: p.sponsorship_ids.filtered(
                lambda s: s.state not in ('terminated', 'cancelled')))
        # Test that only one partner matches.
        if partner:
            if len(partner) == 1:
                # If we fall under this rule of completion, it means there is
                # no open invoice corresponding to the payment. We may need to
                # generate one depending on the payment type.
                line_vals, new_invoice = self._generate_invoice(
                    stmts_vals, st_line, partner, ref_index)
                res.update(line_vals)
                # Get the accounting partner (company)
                res['partner_id'] = partner.commercial_partner_id.id
            else:
                logger.warning(
                    'Line named "%s" (Ref:%s) was matched by more '
                    'than one partner while looking on partners' %
                    (st_line['name'], st_line['ref']))
        return res

    def get_from_bvr_ref(self, stmts_vals, st_line):
        """
        If line ref match an invoice BVR Reference, update partner and account
        Then, call the generic st_line method to complete other values.
        """
        ref = ''
        if 'ref' in st_line:
            ref = st_line['ref']
        res = dict()
        partner = self._search_partner_by_bvr_ref(ref)

        if partner:
            res['partner_id'] = partner.commercial_partner_id.id

        return res

    def lsv_dd_get_from_bvr_ref(self, stmts_vals, st_line):
        """
        If line ref match an invoice BVR Reference, update partner and account
        Then, call the generic st_line method to complete other values.
        For LSV/DD statements, search in all invoices.
        """
        ref = st_line['ref']
        res = dict()
        partner = self._search_partner_by_bvr_ref(ref, True)

        if partner:
            res['partner_id'] = partner.commercial_partner_id.id

        return res

    def get_from_lsv_dd(self, stmts_vals, st_line):
        """ If line is a LSV or DD credit, change the account to 1098. """
        def get_postfinance_id():
            return self.env['res.partner'].search([
                ('name', '=', 'Postfinance SA')
            ], limit=1).commercial_partner_id.id

        def fetch_account_id_by_code(code):
            return self.env['account.account'] \
                .search([('code', '=', code)], limit=1).id

        label = st_line['name'].replace('\n', ' ') if st_line[
            'name'] != '/' else st_line['ref'].replace('\n', ' ')
        lsv_dd_strings = [u'BULLETIN DE VERSEMENT ORANGE',
                          u'ORDRE DEBIT DIRECT',
                          u'CRÉDIT GROUPÉ BVR',
                          u'Crèdit LSV']

        if st_line['amount'] >= 0:
            if u'KREDITKARTEN' in label:
                return {
                    'account_id': fetch_account_id_by_code('2000'),
                    'partner_id': get_postfinance_id()
                }
            elif u'CRÉDIT TRANSACTIONS E-PAYMENT POSTFINANCE CARD' in label:
                return {
                    'account_id': fetch_account_id_by_code('1015'),
                    'partner_id': get_postfinance_id()
                }
            else:
                is_lsv_dd = any(s in label for s in lsv_dd_strings)
                if is_lsv_dd:
                    account_id = fetch_account_id_by_code('1098')
                    if account_id:
                        return {
                            'account_id': fetch_account_id_by_code('1098')
                        }
        return {}

    def get_sponsor_name(self, st_vals, st_line):
        res = {}
        name = st_line['name']
        wire_transfer_pattern = u"VIREMENT DU COMPTE "
        patterns_lookup = [u" EXPÉDITEUR: ", u" DONNEUR D'ORDRE: ",
                           wire_transfer_pattern]

        def search_partner(criteria):
            return self.env['res.partner'].search(criteria)

        for pattern in patterns_lookup:
            if pattern in name:
                sender_info = name.split(pattern)[1]
                if pattern == wire_transfer_pattern:
                    # First the account of partner, then the name
                    # (lastname is at first)
                    name_guess = sender_info.split(" ")[1:3]
                    name_guess.reverse()
                else:
                    # Guess the name with the two first words (following words
                    # could be part of the address (firstname is at first)
                    name_guess = sender_info.split(" ")[:2]
                partner = search_partner([
                    ('firstname', 'ilike', name_guess[0]),
                    ('lastname', '=ilike', name_guess[1])
                ]) if len(name_guess) >= 2 else []
                if len(partner) > 1:
                    # Try to do exact search on firstname
                    partner = search_partner([
                        ('firstname', '=ilike', name_guess[0]),
                        ('lastname', '=ilike', name_guess[1])
                    ])
                if not partner:
                    # Try to find a company
                    partner = search_partner([
                        ('name', 'ilike', name_guess[0]),
                        ('is_company', '=', True)
                    ])
                if partner and len(partner) == 1:
                    res['partner_id'] = partner.commercial_partner_id.id

        return res

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    def _generate_invoice(self, stmts_vals, st_line, partner, ref_index):
        """
        Generates an invoice corresponding to the statement line read
        in order to reconcile the corresponding move lines.

        :param stmts_vals: bank statement values
        :param st_line: current statement line values
        :param partner: matched partner
        :param ref_index: starting index at which the partner ref was found
        :return: dict, boolean: st_line values to update, true if invoice is
                                created.
        """
        # Read data in english
        res = dict()
        ref = st_line['ref']
        product = self.with_context(lang='en_US')._find_product_id(
            partner.ref, ref)
        if not product:
            return res, False
        # Don't gengerate invoice if it's a Sponsor gift
        if product.categ_name == GIFT_CATEGORY:
            res['name'] = product.name
            contract_obj = self.env['recurring.contract'].with_context(
                lang='en_US')
            # the contract number should be found after the ref on 5 digits.
            contract_index = ref_index + 7
            contract_number = int(
                ref[contract_index:contract_index+5])
            search_criterias = [
                '|',
                ('partner_id', '=', partner.id),
                ('correspondent_id', '=', partner.id),
                ('state', '!=', 'draft'),
                ('type', 'like', 'S')
            ]
            contract = contract_obj.search(search_criterias + [
                ('commitment_number', '=', contract_number)])
            if not contract:
                # Maybe the ref is misaligned. Most people have a number < 10
                # so we try to find this digit in the ref and see if we get
                # lucky.
                contract_number_match = re.search(
                    partner.ref + r'0{1,4}(\d)', ref)
                if contract_number_match:
                    contract_number = int(contract_number_match.group(1))
                    contract = contract_obj.search(search_criterias + [
                        ('commitment_number', '=', contract_number)])
            if len(contract) == 1:
                # Retrieve the birthday of child
                birthdate = ""
                if product.default_code == GIFT_REF[0]:
                    birthdate = contract.child_id.birthdate
                    birthdate = datetime.strptime(birthdate, DF).strftime(
                        "%d %b").decode('utf-8')
                res['name'] += "[" + contract.child_code
                res['name'] += " (" + birthdate + ")]" if birthdate else "]"
            else:
                res['name'] += " [Child not found] "
            return res, False

        # Setup invoice data
        journal_id = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1).id

        inv_data = {
            'account_id': partner.property_account_receivable_id.id,
            'type': 'out_invoice',
            'partner_id': partner.id,
            'journal_id': journal_id,
            'date_invoice': st_line['date'],
            'payment_term_id': 1,  # Immediate payment
            'payment_mode_id': self.env['account.payment.mode'].search(
                [('name', '=', 'BVR')]).id,
            'reference': ref,
            'origin': stmts_vals['name']
        }

        # Create invoice and generate invoice lines
        invoice = self.env['account.invoice'].with_context(
            lang='en_US').create(inv_data)

        res.update(self._generate_invoice_line(
            invoice.id, product, st_line, partner.id))

        invoice.action_invoice_open()

        return res, True

    def _generate_invoice_line(self, invoice_id, product, st_line, partner_id):
        inv_line_data = {
            'name': product.name,
            'account_id': product.property_account_income_id.id,
            'price_unit': st_line['amount'],
            'price_subtotal': st_line['amount'],
            'quantity': 1,
            'product_id': product.id or False,
            'invoice_id': invoice_id,
        }

        res = {}

        # Define analytic journal
        analytic = self.env['account.analytic.default'].account_get(
            product.id, partner_id, date=fields.Date.today())
        if analytic and analytic.analytic_id:
            inv_line_data['account_analytic_id'] = analytic.analytic_id.id

        res['name'] = product.name

        self.env['account.invoice.line'].create(inv_line_data)

        return res

    def _search_partner_by_bvr_ref(self, bvr_ref, search_old_invoices=False):
        """ Finds a partner given its bvr reference. """
        partner = None
        contract_group_obj = self.env['recurring.contract.group']
        contract_groups = contract_group_obj.search(
            [('bvr_reference', '=', bvr_ref)])
        if contract_groups:
            partner = contract_groups[0].partner_id
        else:
            # Search open Customer Invoices (with field 'bvr_reference' set)
            invoice_obj = self.env['account.invoice']
            invoice_search = [
                ('reference', '=', bvr_ref),
                ('state', '=', 'open')]
            if search_old_invoices:
                invoice_search[1] = ('state', 'in', ('open', 'cancel', 'paid'))
            invoices = invoice_obj.search(invoice_search)
            if not invoices:
                # Search open Supplier Invoices (with field 'reference_type'
                # set to BVR)
                invoices = invoice_obj.search([
                    '|',
                    ('reference', '=', bvr_ref),
                    ('bvr_reference', '=', bvr_ref),
                    ('state', '=', 'open')])
            if invoices:
                partner = invoices[0].partner_id

        return partner

    def _find_product_id(self, partner_ref, ref):
        """ Finds what kind of payment it is,
            based on the reference of the statement line. """
        product_obj = self.env['product.product'].with_context(lang='en_US')
        # Search for payment type in a flexible manner given its neighbours
        payment_type_match = re.search(
            partner_ref + r'0{1,4}[1-9]{1,3}([1-9])0', ref)
        if payment_type_match:
            payment_type = int(payment_type_match.group(1))
            payment_type_index = payment_type_match.start(1)
        else:
            # Take payment type from its fixed position where it's supposed.
            payment_type_index = -6
            payment_type = int(ref[payment_type_index])
        product = 0
        if payment_type in range(1, 6):
            # Sponsor Gift
            products = product_obj.search(
                [('default_code', '=', GIFT_REF[payment_type - 1])])
            product = products[0] if products else 0
        elif payment_type in range(6, 8):
            # Fund donation
            products = product_obj.search(
                [('fund_id', '=', int(
                    ref[payment_type_index+1:payment_type_index+5]))])
            product = products[0] if products else 0

        return product
