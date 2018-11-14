# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields
from odoo.addons.sponsorship_compassion.models.product import \
    GIFT_CATEGORY


class AccountInvoice(models.Model):
    """ Add mailing origin in invoice objects. """
    _inherit = 'account.invoice'

    @api.model
    def create_from_wordpress(
            self, partner_id, wp_origin, amount, fund, child_code,
            pf_payid, payment_mode_name, utm_source, utm_medium, utm_campaign
    ):
        """
         Utility for invoice donation creation.
        :param partner_id: odoo partner_id
        :param wp_origin: the fund code in wordpress
        :param amount: amount of donation
        :param fund: the fund code in wordpress
        :param child_code: child local_id
        :param pf_payid: postfinance transaction number
        :param payment_mode_name: the payment_mode identifier from postfinance
        :param utm_source: the utm identifier in wordpress
        :param utm_medium: the utm identifier in wordpress
        :param utm_campaign: the utm identifier in wordpress
        :return: invoice_id
        """
        partner = self.env['res.partner'].browse(partner_id)
        if partner.contact_type == 'attached':
            if partner.type == 'email_alias':
                # In this case we want to link to the main partner
                partner = partner.contact_id
                partner_id = partner.id
            else:
                # We unarchive the partner to make it visible
                partner.active = True
        product = self.env['product.product']
        if fund:
            product = product.search([
                ('default_code', 'ilike', fund)])
        sponsorship = self.env['recurring.contract']
        if child_code:
            sponsorship = sponsorship.search([
                '|', ('partner_id', '=', partner_id),
                ('correspondent_id', '=', partner_id),
                ('child_code', '=', child_code)
            ], order='id desc', limit=1)
        payment_mode = self.env['account.payment.mode'].search([
            ('name', '=', payment_mode_name),
            ('active', '=', True)
        ])
        if not payment_mode:
            # Credit Card Journal
            journal = self.env['account.journal'].search([
                ('code', '=', 'CCRED')
            ], limit=1)
            payment_mode.create({
                'name': payment_mode_name,
                'payment_method_id': 1,  # Manual inbound
                'payment_type': 'inbound',
                'bank_account_link': 'fixed',
                'fixed_journal_id': journal.id,
                'active': True
            })
        origin = 'WP ' + wp_origin + ' ' + str(pf_payid)
        invoice = self.search([
            ('user_id', '=', self.env.uid),
            ('partner_id', '=', partner_id),
            ('state', '=', 'draft')
        ])
        utms = self.env['utm.mixin'].get_utms(
            utm_source, utm_medium, utm_campaign)
        if not invoice:
            account = self.env['account.account'].search([
                ('code', '=', '1050')])
            internet_id = self.env.ref('utm.utm_medium_website').id
            # Compute invoice date for birthday gifts
            invoice_date = fields.Date.today()
            invoice = self.create({
                'partner_id': partner_id,
                'payment_mode_id': payment_mode.id,
                'origin': origin,
                'reference': str(pf_payid),
                'transaction_id': str(pf_payid),
                'date_invoice': invoice_date,
                'currency_id': 6,  # Always in CHF
                'account_id': account.id,
                'name': 'Postfinance payment ' + str(pf_payid) + ' for ' +
                wp_origin,
            })
        analytic_id = self.env['account.analytic.default'].account_get(
            product.id).analytic_id.id
        gift_account = self.env['account.account'].search([
            ('code', '=', '6003')])
        self.env['account.invoice.line'].create({
            'invoice_id': invoice.id,
            'product_id': product.id,
            'account_id': product.property_account_income_id.id or
            gift_account.id,
            'contract_id': sponsorship.id,
            'name': product.name or 'Online donation for ' + wp_origin,
            'quantity': 1,
            'price_unit': amount,
            'account_analytic_id': analytic_id,
            'source_id': utms['source'],
            'medium_id': utms.get('medium', internet_id),
            'campaign_id': utms['campaign'],
        })
        requires_sponsorship = GIFT_CATEGORY in invoice.mapped(
            'invoice_line_ids.product_id.categ_name')
        partner.set_privacy_statement(origin='new_gift')
        new_partner = partner.state != 'active'
        if analytic_id and (not requires_sponsorship or
                            sponsorship) and not new_partner:
            invoice.action_invoice_open()
            payment_vals = {
                'journal_id': self.env['account.journal'].search(
                    [('name', '=', 'Web')]).id,
                'payment_method_id': self.env['account.payment.method'].search(
                    [('code', '=', 'sepa_direct_debit')]).id,
                'payment_date': invoice.date,
                'communication': invoice.reference,
                'invoice_ids':  [(6, 0, invoice.ids)],
                'payment_type': 'inbound',
                'amount': invoice.amount_total,
                'currency_id': invoice.currency_id.id,
                'partner_id': invoice.partner_id.id,
                'partner_type': 'customer',
                'payment_difference_handling': 'reconcile',
                'payment_difference': invoice.amount_total,
            }
            account_payment = self.env['account.payment'].create(payment_vals)
            account_payment.post()
        return invoice.id
