# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
import pprint

from odoo import http
from odoo.http import request
from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)

class PaymentOgoneCompassionController(http.Controller):
    _accept_url = '/payment/donation/test/accept'
    _decline_url = '/payment/donation/test/decline'
    _exception_url = '/payment/donation/test/exception'
    _cancel_url = '/payment/donation/test/cancel'
    # TODO
    # need to skim
    # https://compassion.ch/fr/annulation-don
    # https://compassion.ch/fr/confirmation-don
    @http.route([
        '/payment/donation/accept', '/payment/donation/test/accept/',
    ], type='http', auth='public', website=True)
    def ogone_form_feedback_accept(self, **post):
        """ Ogone contacts using GET, at least for accept """
        _logger.info('Ogone: entering form_feedback with post data %s', pprint.pformat(post))  # debug
        if request.env['payment.transaction'].sudo().form_feedback(post,
                                                                  'ogone'):
            http.request.env['payment.acquirer']\
                .validate_invoice_line(post['orderID'])
        return http.request.render('payment_ogone_compassion.accept')

    @http.route([
        '/payment/donation/exception', '/payment/donation/test/exception',
        '/payment/donation/decline', '/payment/donation/test/decline',
        '/payment/donation/cancel', '/payment/donation/test/cancel',
    ], type='http', auth='none')
    def ogone_form_feedback_decline(self, **post):
        """ Ogone contacts using GET, at least for accept """
        return http.request.render('payment_ogone_compassion.decline')
