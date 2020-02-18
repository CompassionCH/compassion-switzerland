##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import time
import urllib.parse

import requests

from ..controllers.main import OgoneCompassion
from odoo import api, models, fields
from odoo.http import request
from odoo.tools import float_round
from odoo.tools.float_utils import float_repr
from odoo.addons.payment_ogone.models.payment import PaymentTxOgone
from odoo.addons.queue_job.job import job

# Add 91 as a valid status, because Postfinance Card is only sending this
PaymentTxOgone._ogone_valid_tx_status = [5, 9, 91, 95, 99, 50, 51, 52, 56]


class PaymentAcquirerOgone(models.Model):
    _inherit = 'payment.acquirer'

    def _get_ogone_urls(self, environment):
        """ Ogone URLS:
         - standard order: POST address for form-based """
        return {
            'ogone_standard_order_url':
                f'https://e-payment.postfinance.ch/ncol/{environment}'
                f'/orderstandard_utf8.asp',
            'ogone_direct_order_url':
                f'https://e-payment.postfinance.ch/ncol/{environment}/orderdirect_utf8'
                '.asp',
            'ogone_direct_query_url':
                f'https://e-payment.postfinance.ch/ncol/{environment}/querydirect_utf8'
                '.asp',
            'ogone_afu_agree_url':
                f'https://e-payment.postfinance.ch/ncol/{environment}''/AFU_agree.asp',
        }

    def ogone_form_generate_values(self, values):
        """ Replace return urls with current domain to avoid changing domain
        for the website visitor. Code copied from ogone module. """
        base_url = request.httprequest.host_url
        ogone_tx_values = dict(values)
        temp_ogone_tx_values = {
            'PSPID': self.ogone_pspid,
            'ORDERID': values['reference'],
            'AMOUNT': float_repr(float_round(values['amount'], 2) * 100, 0),
            'CURRENCY': values['currency'] and values['currency'].name or '',
            'LANGUAGE': values.get('partner_lang'),
            'CN': values.get('partner_name'),
            'EMAIL': values.get('partner_email'),
            'OWNERZIP': values.get('partner_zip'),
            'OWNERADDRESS': values.get('partner_address'),
            'OWNERTOWN': values.get('partner_city'),
            'OWNERCTY': values.get('partner_country') and values.get(
                'partner_country').code or '',
            'OWNERTELNO': values.get('partner_phone'),
            'ACCEPTURL': '%s' % urllib.parse.urljoin(
                base_url, OgoneCompassion._accept_url),
            'DECLINEURL': '%s' % urllib.parse.urljoin(
                base_url, OgoneCompassion._decline_url),
            'EXCEPTIONURL': '%s' % urllib.parse.urljoin(
                base_url, OgoneCompassion._exception_url),
            'CANCELURL': '%s' % urllib.parse.urljoin(
                base_url, OgoneCompassion._cancel_url),
            'PARAMPLUS': 'return_url=%s' % ogone_tx_values.pop(
                'return_url') if ogone_tx_values.get('return_url') else False,
        }
        if self.save_token in ['ask', 'always']:
            temp_ogone_tx_values.update({
                'ALIAS': f'ODOO-NEW-ALIAS-{time.time()}',
                # something unique,
                'ALIASUSAGE': values.get(
                    'alias_usage') or self.ogone_alias_usage,
            })
        shasign = self._ogone_generate_shasign('in', temp_ogone_tx_values)
        temp_ogone_tx_values['SHASIGN'] = shasign
        ogone_tx_values.update(temp_ogone_tx_values)
        return ogone_tx_values


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    postfinance_payid = fields.Char()
    postfinance_brand = fields.Char()
    payment_mode_id = fields.Many2one(
        'account.payment.mode', 'Payment mode',
        compute='_compute_payment_mode', store=True)

    @api.multi
    @api.depends('postfinance_brand')
    def _compute_payment_mode(self):
        for tx in self.filtered('postfinance_brand'):
            tx.payment_mode_id = tx.payment_mode_id.search([
                ('name', 'ilike', tx.postfinance_brand)
            ], limit=1)

    @api.model
    @job(default_channel='root.ogone_payment')
    def push_s2s_to_wordpress(self, post_data):
        """Push Ogone S2S feedback to Wordpress"""
        # First try to find if invoice is already imported in Odoo
        transaction_id = post_data.get('PAYID')
        if transaction_id:
            invoice = self.env['account.invoice'].search([
                ('transaction_id', '=', transaction_id)
            ])
            if invoice:
                return "Invoice already imported in Odoo"

        # Send Data to Wordpress
        host = self.env['wordpress.configuration'].get_host()
        res = requests.get(
            "https://" + host + '/confirmation-don', post_data
        )
        return "Payment data sent to Wordpress : " + str(res.status_code)
