# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http, _, fields
from odoo.http import request


class MuskathlonWebsite(http.Controller):
    @http.route('/muskathlon_registration/event/<model('
                '"crm.event.compassion"):event>/',
                auth='public', website=True, methods=['GET'])
    @http.route('/muskathlon_registration/', defaults={'event': None},
                auth='public', website=True, methods=['GET'])
    def new_registration(self, event):
        """
        Displays the registration form.
        """
        values = {
            'event': event,
            'sports': event.sport_discipline_ids,
            'countries': request.env['res.country'].search([]),
            'states': request.env['res.country.state'].search([]),
            'languages': request.env['res.lang'].search([]),
            'acquirers': []
        }
        # Fetch the payment acquirers to display a selection with pay button
        # See https://github.com/odoo/odoo/blob/10.0/addons/
        # website_sale/controllers/main.py#L703
        # for reference
        acquirers = request.env['payment.acquirer'].search(
            [('website_published', '=', True)]
        )
        for acquirer in acquirers:
            acquirer_button = acquirer.with_context(
                submit_class='btn btn-primary',
                submit_txt=_('Pay Now')).sudo().render(
                '/',
                100.0,  # This is the registration fee
                request.env.ref('base.CHF').id,  # This is in CHF
                values={
                    'return_url': '/muskathlon_registration/payment/validate',
                }
            )
            acquirer.button = acquirer_button
            values['acquirers'].append(acquirer)

        return http.request.render('muskathlon.new_registration', values)

    @http.route(['/muskathlon_registration/payment/<int:acquirer_id>'],
                type='json', auth="public", website=True)
    def registration_payment(self, acquirer_id, tx_type='form', token=None,
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

        sport_id = int(kwargs['sport_id'])
        event = env['crm.event.compassion'].browse(
            int(kwargs['event_id']))

        # Create the muskathlon registration
        registration = env['muskathlon.registration'].create({
            'event_id': event.id,
            'partner_id': partner.id,
            'sport_discipline_id': sport_id,
            'sport_level': kwargs['level'],
            'sport_level_description': kwargs['sport_description']
        })

        # find an already existing transaction
        tx_values = {
            'acquirer_id': acquirer_id,
            'type': tx_type,
            'amount': 100.0,
            'currency_id': request.env.ref('base.CHF').id,
            'partner_id': partner.id,
            'partner_country_id': partner.country_id.id,
            'reference': 'MUSK-REG-' + str(registration.id),
            'registration_id': registration.id,
        }
        return request.website.get_transaction_for_payment(
            token, partner, tx_values,
            '/muskathlon_registration/payment/validate'
        )

    @http.route('/muskathlon_registration/payment/validate',
                type='http', auth="public", website=True)
    def payment_validate(self, transaction_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction.
        """
        uid = request.env.ref('muskathlon.user_muskathlon_portal').id
        env = request.env(user=uid)
        if transaction_id is None:
            transaction_id = request.session.get('sale_transaction_id')
        if transaction_id:
            tx = env['payment.transaction'].browse(transaction_id)

        if not tx or not tx.registration_id:
            return http.request.render('muskathlon.registration_failure')

        event = tx.registration_id.event_id
        if tx.state == 'done':
            # Create invoice and lead
            partner = tx.partner_id
            fee_template = env.ref('muskathlon.product_registration')
            product = fee_template.product_variant_ids[:1]
            invoice = env['account.invoice'].create({
                'partner_id': partner.id,
                'currency_id': tx.currency_id.id,
                'invoice_line_ids': [(0, 0, {
                    'quantity': 1.0,
                    'price_unit': 100,
                    'account_analytic_id': event.analytic_id.id,
                    'account_id': product.property_account_income_id.id,
                    'name': 'Muskathlon registration fees',
                    'product_id': product.id
                })]
            })
            payment_vals = {
                'journal_id': env['account.journal'].search(
                    [('name', '=', 'Web')]).id,
                'payment_method_id': env['account.payment.method'].search(
                    [('code', '=', 'sepa_direct_debit')]).id,
                'payment_date': fields.Date.today(),
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
            if partner.write_uid.id != uid:
                # Validate invoice and post the payment.
                invoice.action_invoice_open()
                account_payment.post()
            staff_id = env['staff.notification.settings'].get_param(
                'muskathlon_lead_notify_ids')
            sport_desc = tx.registration_id.sport_level_description
            tx.registration_id.lead_id = env['crm.lead'].create({
                'name': u'Muskathlon Registration - ' + partner.name,
                'partner_id': partner.id,
                'email_from': partner.email,
                'phone': partner.phone,
                'partner_name': partner.name,
                'street': partner.street,
                'zip': partner.zip,
                'city': partner.city,
                'user_id': staff_id and staff_id[0] or 1,
                'description': sport_desc
            })
            if not partner.ambassador_details_id:
                partner.ambassador_details_id = env[
                    'ambassador.details'].create({
                        'partner_id': partner.id,
                    })
            # TODO prepare communication for sponsor.
        elif tx and tx.state == 'cancel':
            # cancel the registration
            tx.registration_id.unlink()

        # clean context and session, then redirect to the confirmation page
        request.session['sale_transaction_id'] = False
        if tx and tx.state == 'draft':
            return request.redirect('/event/' + str(event.id))

        return request.redirect(
            '/muskathlon_registration/confirmation/' +
            str(tx.registration_id.event_id.id))

    @http.route('/muskathlon_registration/confirmation/'
                '<int:event_id>',
                type='http', auth="public", website=True)
    def payment_confirmation(self, event_id, **kwargs):
        event = request.env['crm.event.compassion'].browse(event_id)
        return http.request.render('muskathlon.new_registration_successful', {
            'event': event
        })
