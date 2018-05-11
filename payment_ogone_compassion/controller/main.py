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
from odoo.addons.payment_ogone.controllers.main import OgoneController
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

OgoneController._accept_url = '/payment/donation/test/accept'
OgoneController._cancel_url = '/payment/donation/test/cancel'
OgoneController._decline_url = '/payment/donation/test/decline'
OgoneController._except_url = '/payment/donation/test/except'


class OgoneController2(http.Controller):
    @http.route([
        '/payment/donation/<string:result>/',
        '/payment/donation/test/<string:result>/',
    ], type='http', auth='public', website=True)
    def ogone_form_feedback(self, result, **post):
        """ Ogone contacts using GET, at least for accept """
        _logger.info('Donation from Ogone: entering form_feedback with post '
                     'data %s',
                     pprint.pformat(post))  # debug
        if result != 'accept':
            result = 'decline'

        try:
            feedback = request.env['payment.transaction'].sudo().form_feedback(
                post, 'ogone')
        except ValidationError:
            feedback = False

        invoice_line = http.request.env['account.invoice.line'].browse(int(
            post['orderID']))
        registration = invoice_line.event_id.muskathlon_registration_ids \
            .filtered(lambda item: item.partner_id == invoice_line.user_id)

        if feedback:
            http.request.env['payment.acquirer'] \
                .validate_order_id(post['orderID'])
        return http.request.render('payment_ogone_compassion.' + result, {
            'event': invoice_line.event_id,
            'registration': registration
        })
