# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.http import Controller, request, route
from odoo.addons.payment.models.payment_acquirer import ValidationError


class PaymentController(Controller):

    @route('/mobile-app/payment/<int:invoice_id>', type='http',
           website=True, methods=['GET'],
           auth='public', noindex=['header', 'meta', 'robots'])
    def app_payment(self, invoice_id):
        """
        Route for mobile APP payment redirecting to Postfinance.

        :param invoice_id: account.invoice record created previously by the
                           donation made from the app.
        :return: werkzeug response
        """
        invoice = request.env['account.invoice'].sudo().browse(invoice_id)
        postfinance = request.env.ref(
            'payment_ogone_compassion.payment_postfinance')
        transaction_obj = request.env['payment.transaction'].sudo()
        reference = transaction_obj.get_next_reference('APP-' + invoice.origin)
        transaction_id = transaction_obj.create({
            'acquirer_id': postfinance.id,
            'type': 'form',
            'amount': invoice.amount_total,
            'currency_id': invoice.currency_id.id,
            'partner_id': invoice.partner_id.id,
            'reference': reference,
            'invoice_id': invoice.id,
        }).id
        return request.redirect(
            '/compassion/payment/{}?redirect_url={}&display_type=full_page'
            .format(transaction_id, '/mobile-app/payment/validate')
        )

    @route('/mobile-app/payment/validate', type='http', auth='public',
           website=True,
           noindex=['header', 'meta', 'robots'])
    def app_payment_validate(self, **post):
        payment_status = 'ok'
        tx = request.env['payment.transaction'].sudo()
        try:
            tx = tx._ogone_form_get_tx_from_data(post)
        except ValidationError:
            payment_status = 'fail'
        if not tx.invoice_id:
            payment_status = 'fail'
        return request.render(
            'mobile_app_payment_controller.payment_redirect',
            {'payment_status': payment_status}
        )
