# -*- coding: utf-8 -*-
import logging
import pprint
import urllib

import werkzeug

from odoo import http
from odoo.http import request
from odoo.addons.payment_ogone.controllers.main import OgoneController

_logger = logging.getLogger(__name__)


def encoded_dict(in_dict):
    out_dict = {}
    for k, v in in_dict.iteritems():
        if isinstance(v, unicode):
            v = v.encode('utf8')
        elif isinstance(v, str):
            # Must be encoded in UTF-8
            v.decode('utf8')
        out_dict[k] = v
    return out_dict


class OgoneCompassion(OgoneController):
    @http.route([
        '/payment/ogone/accept', '/payment/ogone/test/accept',
        '/payment/ogone/decline', '/payment/ogone/test/decline',
        '/payment/ogone/exception', '/payment/ogone/test/exception',
        '/payment/ogone/cancel', '/payment/ogone/test/cancel',
    ], type='http', auth='none')
    def ogone_form_feedback(self, **post):
        """ Override to pass params to redirect url """
        transaction_obj = request.env['payment.transaction'].sudo()
        _logger.info('Ogone: entering form_feedback with post data %s',
                     pprint.pformat(post))  # debug
        tx = transaction_obj._ogone_form_get_tx_from_data(post)
        tx.write({
            'postfinance_payid': post.get('PAYID'),
            'postfinance_brand': post.get('BRAND')
        })
        transaction_obj.form_feedback(post, 'ogone')
        redirect = post.pop('return_url', '/') + '?' + urllib.urlencode(
            encoded_dict(post))
        return werkzeug.utils.redirect(redirect)
