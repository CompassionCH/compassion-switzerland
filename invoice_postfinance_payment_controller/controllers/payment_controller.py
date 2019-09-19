# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from werkzeug.exceptions import NotFound

from odoo.exceptions import MissingError
from odoo.http import Controller, request, route
from odoo.addons.payment.models.payment_acquirer import ValidationError


class PaymentController(Controller):

    @route('/postfinance/payment/<int:invoice_id>', type='http',
           website=True, methods=['GET', 'POST'],
           auth='public', noindex=['header', 'meta', 'robots'])
    def postfinance_payment(self, invoice_id, **get_params):
        """
        Route for redirecting to Postfinance for paying an invoice.

        :param invoice_id: account.invoice record created previously.
        :return: werkzeug response
        """
        try:
            invoice = request.env['account.invoice'].sudo().browse(invoice_id)
        except MissingError:
            invoice = request.env['account.invoice']
        if not invoice.exists() or invoice.state == 'paid':
            raise NotFound()
        postfinance = request.env.ref(
            'payment_ogone_compassion.payment_postfinance')
        transaction_obj = request.env['payment.transaction'].sudo()
        reference = transaction_obj.get_next_reference(invoice.origin or 'WEB')
        transaction_id = transaction_obj.create({
            'acquirer_id': postfinance.id,
            'type': 'form',
            'amount': invoice.amount_total,
            'currency_id': invoice.currency_id.id,
            'partner_id': invoice.partner_id.id,
            'reference': reference,
            'invoice_id': invoice_id,
            'accept_url': get_params.get('accept_url', invoice.accept_url),
            'decline_url': get_params.get('decline_url', invoice.decline_url),
        }).id
        return request.redirect(
            '/compassion/payment/{}?redirect_url={}&display_type=full_page'
            .format(
                transaction_id, '/postfinance/payment/validate'
            )
        )

    @route('/postfinance/payment/validate',
           type='http', auth='public', website=True,
           noindex=['header', 'meta', 'robots'])
    def payment_validate(self, **post):
        payment_ok = True
        tx = request.env['payment.transaction'].sudo()
        try:
            tx = tx._ogone_form_get_tx_from_data(post)
        except ValidationError:
            payment_ok = False
        if not tx.invoice_id or tx.state not in ('done', 'authorized'):
            payment_ok = False

        if payment_ok and tx.accept_url:
            return request.redirect(tx.accept_url)
        if not payment_ok and tx.decline_url:
            return request.redirect(tx.decline_url)

        # If no redirection is set, use the default template
        return request.render(
            'invoice_postfinance_payment_controller.payment_redirect',
            {'payment_ok': payment_ok,
             'tx': tx,
             }
        )
