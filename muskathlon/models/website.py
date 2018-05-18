# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, _
from odoo.http import request


class Website(models.Model):
    _inherit = 'website'

    def find_partner(self, form_data):
        """
        Find and returns a matching partner, or create one.
        :param form_data: dict that must contain
            email, lastname, firstname, zip, phone, street, city, country_id
        :return: partner record
        """
        uid = self.env.ref('muskathlon.user_muskathlon_portal').id
        self = self.sudo(uid)
        partner_obj = self.env['res.partner']
        partner = partner_obj.search([
            ('email', '=ilike', form_data['email'])], limit=1)
        if not partner:
            partner = partner_obj.search([
                ('lastname', '=ilike', form_data['lastname']),
                ('firstname', '=ilike', form_data['firstname']),
                ('zip', '=', form_data['zip'])], limit=1)
        if not partner:
            # no match found -> creating a new one.
            partner = partner_obj.create({
                'firstname': form_data['firstname'],
                'lastname': form_data['lastname'],
                'email': form_data['email'],
                'phone': form_data['phone'],
                'street': form_data['street'],
                'city': form_data['city'],
                'zip': form_data['zip'],
                'country_id': int(form_data['country_id'])
            })
        return partner

    def get_transaction_for_payment(self, token, partner,
                                    tx_vals, redirect):
        """
         Finds or create a transaction when payment form is submitted.
         Redirect to the acquirer website
        :param token: if any payment.token exists
        :param partner: res.partner record of person making payment
        :param tx_vals: payment.transaction values
        :param redirect: url for redirection after payment
        :return: web rendered
        """
        transaction_obj = self.env['payment.transaction'].sudo()
        transaction = request.session.get('sale_transaction_id')
        if transaction:
            transaction = transaction_obj.browse(transaction)
            if token and transaction.payment_token_id and \
                    token != transaction.payment_token_id.id:
                # new or distinct token
                transaction = False
            elif transaction.state == 'draft':
                transaction.write(dict(
                    transaction_obj.on_change_partner_id(partner.id).get(
                        'value', {}
                    ),
                    amount=tx_vals['amount'], type=tx_vals['type'])
                )
        if not transaction:
            if token and self.env['payment.token'].browse(
                    int(token)).partner_id == partner.id:
                tx_vals['payment_token_id'] = token

            tx_vals['reference'] = transaction_obj.get_next_reference(
                tx_vals['reference'])
            transaction = transaction_obj.create(tx_vals)
            request.session['sale_transaction_id'] = transaction.id

        if token:
            return self.env.ref('website_sale.payment_token_form').render(
                dict(tx=transaction), engine='ir.qweb')

        return transaction.acquirer_id.with_context(
            submit_class='btn btn-primary',
            submit_txt=_('Pay Now')).sudo().render(
            transaction.reference,
            transaction.amount,
            transaction.currency_id.id,
            values={
                'return_url': redirect,
                'partner_id': partner.id,
                'billing_partner_id': partner.id,
            },
        )
