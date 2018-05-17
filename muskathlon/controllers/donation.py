# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http
from odoo.http import request


class DonationController(http.Controller):

    @http.route(['/muskathlon_donation/payment/<int:acquirer_id>'],
                type='json', auth="public", website=True)
    def donation_payment(self, acquirer_id, tx_type='form', token=None,
                         **kwargs):
        """ Json method that creates a payment.transaction, used to create a
        transaction when the user clicks on 'pay now' button. After having
        created the transaction, the event continues and the user is redirected
        to the acquirer website.

        :param int acquirer_id: id of a payment.acquirer record.
        """
        uid = request.env.ref('muskathlon.user_muskathlon_portal').id
        env = request.env(user=uid)
        partner = request.website.find_partner(kwargs)

        # Create invoice for the donation
        currency = env['res.currency'].search([(
            'name', '=', kwargs['currency'])], limit=1)
        event = env['crm.event.compassion'].browse(int(kwargs['event_id']))
        ambassador = env['res.partner'].browse(int(kwargs['ambassador_id']))
        muskathlon = env.ref(
            'sponsorship_switzerland.product_template_fund_4mu')
        product = muskathlon.product_variant_ids[:1]
        invoice = env['account.invoice'].create({
            'partner_id': partner.id,
            'currency_id': currency.id,
            'invoice_line_ids': [(0, 0, {
                'quantity': 1.0,
                'price_unit': kwargs['amount'],
                'account_id': product.property_account_income_id.id,
                'name': 'Gift for ' + event.name + ' for ' + ambassador.name,
                'product_id': product.id,
                'account_analytic_id': event.analytic_id.id,
                'user_id': ambassador.id
            })]
        })

        # Create transaction
        tx_vals = {
            'acquirer_id': acquirer_id,
            'type': tx_type,
            'amount': kwargs['amount'],
            'currency_id': currency.id,
            'partner_id': partner.id,
            'partner_country_id': partner.country_id.id,
            'invoice_id': invoice.id,
            'reference': 'MUSK-DON-' + str(invoice.id),
        }
        return request.website.get_transaction_for_payment(
            token, partner, tx_vals, '/muskathlon_donation/payment/validate'
        )

    @http.route('/muskathlon_donation/payment/validate',
                type='http', auth="public", website=True)
    def payment_validate(self, transaction_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction.
        """
        uid = request.env.ref('muskathlon.user_muskathlon_portal').id
        env = request.env(user=uid)
        if transaction_id is None:
            tx = request.website.sale_get_transaction()
        else:
            tx = env['payment.transaction'].browse(transaction_id)

        if not tx or not tx.invoice_id:
            return http.request.render('muskathlon.donation_failure')

        invoice = tx.invoice_id
        if tx.state in ['pending', 'done', 'authorized']:
            # Pay invoice
            invoice.action_invoice_open()
            payment_vals = {
                'journal_id': env['account.journal'].search(
                    [('name', '=', 'Web')]).id,
                'payment_method_id': env['account.payment.method'].search(
                    [('code', '=', 'sepa_direct_debit')]).id,
                'payment_date': invoice.date,
                'communication': invoice.reference,
                'invoice_ids': [(6, 0, invoice.ids)],
                'payment_type': 'inbound',
                'amount': invoice.amount_total,
                'currency_id': invoice.currency_id.id,
                'partner_id': invoice.partner_id.id,
                'partner_type': 'customer',
                'payment_difference_handling': 'reconcile',
                'payment_difference': invoice.amount_total,
            }
            account_payment = env['account.payment'].create(payment_vals)
            account_payment.post()
        elif tx and tx.state == 'cancel':
            # Cancel the invoice
            tx.invoice_id.unlink()

        # clean context and session, then redirect to the confirmation page
        request.website.sale_reset()
        if tx and tx.state == 'draft':
            event = invoice.invoice_line_ids.mapped('event_id')
            ambassador = invoice.invoice_line_ids.mapped('user_id')
            url = '/event/{}/participant/{}'.format(event.id, ambassador.id)
            return request.redirect(url)

        return request.redirect(
            '/muskathlon_donation/confirmation/' + str(invoice.id))

    @http.route('/muskathlon_donation/confirmation/'
                '<int:invoice_id>',
                type='http', auth="public", website=True)
    def payment_confirmation(self, invoice_id):
        invoice = request.env['account.invoice'].browse(invoice_id)
        event = invoice.invoice_line_ids.mapped('event_id')
        ambassador = invoice.invoice_line_ids.mapped('user_id')
        return http.request.render('muskathlon.donation_successful', {
            'ambassador': ambassador,
            'event': event
        })
