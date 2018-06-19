# coding: utf-8
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, fields


class PaymentAcquirerOgone(models.Model):
    _inherit = 'payment.acquirer'

    def _get_ogone_urls(self, environment):
        """ Ogone URLS:
         - standard order: POST address for form-based """
        return {
            'ogone_standard_order_url':
                'https://e-payment.postfinance.ch/ncol/%s/orderstandard_utf8'
                '.asp' % (environment,),
            'ogone_direct_order_url':
                'https://e-payment.postfinance.ch/ncol/%s/orderdirect_utf8'
                '.asp' % (environment,),
            'ogone_direct_query_url':
                'https://e-payment.postfinance.ch/ncol/%s/querydirect_utf8'
                '.asp' % (environment,),
            'ogone_afu_agree_url':
                'https://e-payment.postfinance.ch/ncol/%s''/AFU_agree.asp' % (
                    environment,),
        }


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
