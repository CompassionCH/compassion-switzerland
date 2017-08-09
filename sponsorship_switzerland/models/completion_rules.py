# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from odoo import models, fields
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from odoo.addons.sponsorship_compassion.models.product import \
    GIFT_CATEGORY, GIFT_NAMES

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
        ref = st_line['ref']
        res = {}
        partner_obj = self.env['res.partner']
        partner = partner_obj.search(
            [('ref', '=', str(int(ref[9:16]))),
             ('is_company', '=', False)])
        # Test that only one partner matches.
        if partner:
            if len(partner) == 1:
                # If we fall under this rule of completion, it means there is
                # no open invoice corresponding to the payment. We may need to
                # generate one depending on the payment type.
                res.update(
                    self._generate_invoice(stmts_vals, st_line, partner))
                # Get the accounting partner (company)
                partner = partner_obj._find_accounting_partner(partner)
                res['partner_id'] = partner.id
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
        ref = st_line['ref']
        res = dict()
        partner = self._search_partner_by_bvr_ref(ref)

        if partner:
            partner_obj = self.env['res.partner']
            partner = partner_obj._find_accounting_partner(partner)
            res['partner_id'] = partner.id

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
            partner_obj = self.env['res.partner']
            partner = partner_obj._find_accounting_partner(partner)
            res['partner_id'] = partner.id

        return res

    def get_from_lsv_dd(self, stmts_vals, st_line):
        """ If line is a LSV or DD credit, change the account to 1098. """
        label = st_line['name'].replace('\n', ' ') if st_line[
            'name'] != '/' else st_line['ref'].replace('\n', ' ')
        lsv_dd_strings = [u'BULLETIN DE VERSEMENT ORANGE',
                          u'ORDRE DEBIT DIRECT',
                          u'Crèdit LSV']
        is_lsv_dd = False
        res = {}
        account_id = False
        if u'KREDITKARTEN' in label:
            account_id = self.env['account.account'].search(
                [('code', '=', '2000')], limit=1).id
            res['partner_id'] = self.env['res.partner'].search([
                ('name', '=', 'Postfinance SA')], limit=1).id
        elif u'CRÉDIT TRANSACTIONS E-PAYMENT POSTFINANCE CARD' in label:
            account_id = self.env['account.account'].search(
                [('code', '=', '1015')], limit=1).id
            res['partner_id'] = self.env['res.partner'].search([
                ('name', '=', 'Postfinance SA')], limit=1).id
        else:
            for credit_string in lsv_dd_strings:
                is_lsv_dd = is_lsv_dd or credit_string in label
        if is_lsv_dd:
            account_id = self.env['account.account'].search(
                [('code', '=', '1098')], limit=1).id
        if account_id:
            res['account_id'] = account_id

        return res

    def get_sponsor_name(self, st_vals, st_line):
        res = {}
        name = st_line['name']
        sender_lines = list()

        sender_lines.append(name.replace('\n', ' ').split(
            ' EXPÉDITEUR: '.decode('utf8')))
        sender_lines.append(name.replace('\n', ' ').split(
            " DONNEUR D'ORDRE: ".decode('utf8')))

        id_line1 = 1 if len(sender_lines[0]) > 1 else False
        id_line2 = 2 if len(sender_lines[1]) > 1 else False

        if not id_line1 and not id_line2:
            return res

        id_line = id_line1-1 if id_line1 else id_line2-1
        sender_line = sender_lines[id_line][1].replace(',', '').split(' ')

        index = 0
        for word in sender_line:
            try:
                if index < len(sender_line):
                    int(word)
                for i in range(index-1, 0, -1):
                    firstname = sender_line[i-1]
                    partner = self.env['res.partner'].search(
                        [('lastname', '=ilike', firstname),
                         ('firstname', 'ilike', sender_line[i])])
                    lastnames = sender_line[i].split('-') if not partner else \
                        []

                    for lastname in lastnames:
                        partner = self.env['res.partner'].search(
                            [('lastname', '=ilike', lastname),
                             ('firstname', 'ilike', firstname)]) or \
                            self.env['res.partner'].search(
                            [('lastname', '=ilike', firstname),
                             ('firstname', 'ilike', lastname)])
                    if partner:
                        res['partner_id'] = partner.id
                        return res
            except:
                index += 1

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################

    def _generate_invoice(self, stmts_vals, st_line, partner):
        """ Genereates an invoice corresponding to the statement line read
            in order to reconcile the corresponding move lines. """
        # Read data in english
        res = dict()
        product = self.with_context(lang='en_US')._find_product_id(
            st_line['ref'])
        if not product:
            return res
        # Don't gengerate invoice if it's a Sponsor gift
        if product.categ_name == GIFT_CATEGORY:
            res['name'] = product.name
            contract_obj = self.env['recurring.contract'].with_context(
                lang='en_US')
            contract_number = int(st_line['ref'][16:21])
            contract = contract_obj.search(
                ['|',
                 ('partner_id', '=', partner.id),
                 ('correspondant_id', '=', partner.id),
                 ('commitment_number', '=', contract_number),
                 ('state', '!=', 'draft')])
            if len(contract) == 1:
                # Retrieve the birthday of child
                birthdate = ""
                if product.name == GIFT_NAMES[0]:
                    birthdate = contract.child_id.birthdate
                    birthdate = datetime.strptime(birthdate, DF).strftime(
                        "%d %b").decode('utf-8')
                res['name'] += "[" + contract.child_code
                res['name'] += " (" + birthdate + ")]" if birthdate else "]"
            else:
                res['name'] += " [Child not found] "
            return res

        # Setup invoice data
        journal_id = self.env['account.journal'].search(
            [('type', '=', 'sale')], limit=1).id

        inv_data = {
            'account_id': partner.property_account_receivable.id,
            'type': 'out_invoice',
            'partner_id': partner.id,
            'journal_id': journal_id,
            'date_invoice': st_line['date'],
            'payment_term_id': 1,  # Immediate payment
            # TODO Add payment mode BVR?
            'bvr_reference': st_line['ref'],
            'origin': stmts_vals['name']
        }

        # Create invoice and generate invoice lines
        invoice = self.env['account.invoice'].with_context(
            lang='en_US').create(inv_data)

        res.update(self._generate_invoice_line(
            invoice.id, product, st_line, partner.id))

        invoice.action_invoice_open()

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
            # Search open Customer Invoices (with field 'bvr_reference'
            # set)
            invoice_obj = self.env['account.invoice']
            invoice_search = [
                ('bvr_reference', '=', bvr_ref),
                ('state', '=', 'open')]
            if search_old_invoices:
                invoice_search[1] = ('state', 'in', ('open', 'cancel',
                                                     'paid'))
            invoices = invoice_obj.search(invoice_search)
            if not invoices:
                # Search open Supplier Invoices (with field
                # 'reference_type'
                # set to BVR)
                invoices = invoice_obj.search([
                    ('reference_type', '=', 'bvr'),
                    ('reference', '=', bvr_ref),
                    ('state', '=', 'open')])
            if invoices:
                partner = invoices[0].partner_id

        return partner
