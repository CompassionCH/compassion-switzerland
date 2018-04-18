# coding: utf-8
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Badoux <n.badoux@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


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
                'https://e-payment.postfinance.ch/ncol/%s/orderdirect_utf8.asp'
                '' % (environment,),
            'ogone_direct_query_url':
                'https://e-payment.postfinance.ch/ncol/%s/querydirect_utf8'
                '.asp' % (environment,),
            'ogone_afu_agree_url':
                'https://e-payment.postfinance.ch/ncol/%s''/AFU_agree.asp' % (
                    environment,),
        }

    @api.model
    def create_invoice_and_payment_lines(self, values):
        ogone = self.env.ref('payment.payment_acquirer_ogone')
        partner = self.env['res.partner'].search([
            ('email', '=ilike', values['EMAIL'])], limit=1)
        currency_id = self.env['res.currency'].search([(
            'name', '=', values['CURRENCY'])]).id
        country_id = self.env['res.country'].search([(
            'code', '=', values['OWNERCTY'])]).id
        if not partner:
            partner = self.env['res.partner'].search([
                ('lastname', '=ilike', values['LASTNAME']),
                ('firstname', '=ilike', values['FIRSTNAME'])], limit=1)
        if not partner:
            # no match fonud -> creating a new one.
            partner = self.env['res.partner'].create({
                'firstname': values['FIRSTNAME'],
                'lastname': values['LASTNAME'],
                'email': values['EMAIL'],
                'phone': values['OWNERTELNO'],
                'street': values['OWNERADDRESS'],
                'city': values['OWNERTOWN'],
                'zip': values['OWNERZIP'],
                'country_id': country_id
            })

        invoice_vals = {'partner_id': partner.id,
                        'currency_id': currency_id
                        }

        invoice = self.env['account.invoice'].create(invoice_vals)
        invoice_line_vals = {'quantity': 1.0,
                             'price_unit': values['AMOUNT'],
                             'invoice_id': invoice.id,
                             'account_id': 2775,  # This is specific to
                             # muskathlon. Should be change for something
                             # dependant on some input
                             'name': 'Payment by ogone',
                             'product_id': self.env['product.product'].search(
                                 [('name', '=', values['product_name'])]).id,
                             }
        invoice_line = self.env['account.invoice.line'].create(
            invoice_line_vals)

        if values['ambassador'] and values['event_id']:
            # We are dealing with a payment for a muskathlon -> updating
            # the invoice line to add values so that the gift will be
            # registered toward the muskathlon goal
            self.update_invoice_line_for_muksathlon(invoice_line, values[
                'ambassador'], values['event_id'])

        tx_data = {
            'state': u'draft',
            'acquirer_id': ogone.id,
            'partner_id': partner.id,
            'currency_id': currency_id,
            'partner_country_id': country_id,
            'partner_name': partner.firstname + partner.lastname,
            'partner_phone': values['OWNERTELNO'],
            'partner_addres': values['OWNERADDRESS'],
            'partner_lang': values['LANGUAGE'],
            'partner_email': values['EMAIL'],
            'partner_zip': values['OWNERZIP'],
            'partner_city': values['OWNERTOWN'],
            'partner_state': None,
            'amount': float(values['AMOUNT']),
            'reference': unicode(invoice_line.id)
        }

        tx = self.env['payment.transaction'].create(tx_data)
        tx_data.update({
            'partner_country': tx.partner_country_id,
            'currency': tx.currency_id
        })

        res = ogone.ogone_form_generate_values(tx_data)

        # filter field to send to Ogone
        res = {k: v for k, v in res.iteritems() if k.isupper()}
        del res['PARAMPLUS']
        return ogone.ogone_get_form_action_url(), res

    def validate_invoice_line(self, invoice_id):
        invoice_line = self.env['account.invoice.line'].browse(invoice_id)
        invoice_line.state = 'paid'
        invoice_line.invoice_id.state = 'paid'

    def update_invoice_line_for_muksathlon(self, invoice_line,
                                           ambassador_str, event_id_str):
        ambassador = self.env['res.partner'].browse(ambassador_str)
        event = self.env['crm.event.compassion'].browse(event_id_str)

        val = {
            'account_analytic_id': self.env[
                'account.analytic.account'].browse(event.id).id,
            'name': 'Gift for ' + event.name + ' for ' + ambassador.name,
            'user_id': ambassador.id
        }
        invoice_line.write(val)
