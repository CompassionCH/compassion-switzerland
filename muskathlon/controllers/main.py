# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import _
from odoo.http import request, route
from odoo.addons.website_portal.controllers.main import website_account
from odoo.addons.cms_form.controllers.main import FormControllerMixin
from base64 import b64encode


class MuskathlonWebsite(website_account, FormControllerMixin):
    @route('/events/', auth='public', website=True)
    def list(self, **kwargs):
        events = request.env['crm.event.compassion'].search([
            ('website_published', '=', True),
            ('muskathlon_event_id', '!=', False)
        ])
        return request.render('muskathlon.list', {
            'events': events
        })

    @route('/event/<model("crm.event.compassion"):event>/',
           auth='public', website=True)
    def musk_infos(self, event, **kwargs):
        kwargs.update({
            'event': event,
            'states': request.env['res.country.state'].sudo().search([]),
            'disciplines': event.sport_discipline_ids.ids
        })
        return self.make_response(
            'muskathlon.registration', **kwargs
        )

    @route('/my/muskathlons/<int:muskathlon_id>',
           auth='user', website=True)
    def muskathlon_details(self, muskathlon_id, **kwargs):
        reports = request.env['muskathlon.report'].search(
            [('user_id', '=', request.env.user.partner_id.id),
             ('event_id', '=', muskathlon_id)])
        return request.render('muskathlon.my_details', {
            'reports': reports
        })

    @route('/event/<model("crm.event.compassion"):event>'
           '/<model("muskathlon.registration"):registration>/',
           auth='public', website=True)
    def participant_details(self, event, registration, **kwargs):
        """
        :param event: the event record
        :param registration: a partner record
        :return:the rendered page
        """
        kwargs.update({
            'event': event,
            'registration': registration,
            'states': request.env['res.country.state'].sudo().search([]),
            'form_model_key': 'cms.form.muskathlon.donation'
        })
        return self.make_response(False, **kwargs)

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def account(self, form_id=None, **kw):
        """ Inject data for forms. """
        values = self._prepare_portal_layout_values()
        partner = values['partner']
        ambassador_details_id = partner.ambassador_details_id.id

        # Load forms
        kw['form_model_key'] = 'cms.form.muskathlon.trip.information'
        trip_info_form = self.get_form(
            'ambassador.details', ambassador_details_id, **kw)
        if form_id is None or form_id == trip_info_form.form_id:
            trip_info_form.form_process()

        kw['form_model_key'] = 'cms.form.partner.coordinates'
        coordinates_form = self.get_form('res.partner', partner.id, **kw)
        if form_id is None or form_id == coordinates_form.form_id:
            coordinates_form.form_process()

        kw['form_model_key'] = 'cms.form.ambassador.details'
        about_me_form = self.get_form(
            'ambassador.details', ambassador_details_id, **kw)
        if form_id is None or form_id == about_me_form.form_id:
            about_me_form.form_process()

        values.update({
            'trip_info_form': trip_info_form,
            'coordinates_form': coordinates_form,
            'about_me_form': about_me_form
        })
        return request.render("website_portal.portal_my_home", values)

    @route(['/my/api'], type='http', auth='user', website=True)
    def save_ambassador_picture(self, **post):
        user = request.env.user
        partner = user.partner_id
        return_view = 'website_portal.portal_my_home'

        picture = 'picture_1'
        picture_post = post.get(picture)
        if not picture_post:
            picture = 'picture_2'
            picture_post = post.get(picture)

        if picture_post:
            return_view = 'muskathlon.'+picture+'_formatted'
            image_value = b64encode(picture_post.stream.read())
            if not image_value:
                return 'no image uploaded'
            if picture == 'picture_1':
                partner.write({'image': image_value})
            else:
                partner.ambassador_details_id.write({
                    'picture_large': image_value
                })

        return request.render(return_view,
                              self._prepare_portal_layout_values())

    @route(['/muskathlon/payment/<int:transaction_id>'],
           auth="public", website=True)
    def payment(self, transaction_id, **kwargs):
        """ Controller for redirecting to the payment submission, using
        an existing transaction.

        :param int transaction_id: id of a payment.transaction record.
        """
        transaction = request.env['payment.transaction'].sudo().browse(
            transaction_id)
        values = {
            'payment_form': transaction.acquirer_id.with_context(
                submit_class='btn btn-primary',
                submit_txt=_('Next')).sudo().render(
                transaction.reference,
                transaction.amount,
                transaction.currency_id.id,
                values={
                    'return_url': kwargs['redirect_url'],
                    'partner_id': transaction.partner_id.id,
                    'billing_partner_id': transaction.partner_id.id,
                }
            )
        }
        return request.render('muskathlon.payment_submit', values)

    @route('/muskathlon_registration/payment/validate',
           type='http', auth="public", website=True)
    def registration_payment_validate(self, transaction_id=None, **post):
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
            return request.render('muskathlon.registration_failure')

        event = tx.registration_id.event_id
        post.update({'event': event})
        return self.muskathlon_payment_validate(
            tx, 'muskathlon.new_registration_successful',
            'muskathlon.registration_failure', **post
        )

    @route('/muskathlon_donation/payment/validate',
           type='http', auth="public", website=True)
    def donation_payment_validate(self, transaction_id=None, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction.
        """
        uid = request.env.ref('muskathlon.user_muskathlon_portal').id
        env = request.env(user=uid)
        if transaction_id is None:
            transaction_id = request.session.get('sale_transaction_id')
        if transaction_id:
            tx = env['payment.transaction'].browse(transaction_id)

        if not transaction_id or not tx.invoice_id:
            return request.render('muskathlon.donation_failure')

        invoice_lines = tx.invoice_id.invoice_line_ids
        event = invoice_lines.mapped('event_id')
        ambassador = invoice_lines.mapped('user_id')
        registration = event.muskathlon_registration_ids.filtered(
            lambda r: r.partner_id == ambassador)
        post.update({
            'registration': registration,
            'event': event
        })
        return self.muskathlon_payment_validate(
            tx, 'muskathlon.donation_successful',
            'muskathlon.donation_failure', **post
        )

    def muskathlon_payment_validate(
            self, transaction, success_template, fail_template, **kwargs):
        """
        Common payment validate method: checks state of transaction and
        pay related invoice if everything is fine. Redirects to given urls.
        :param transaction: payment.transaction record
        :param success_template: payment success redirect url
        :param fail_template: payment failure redirect url
        :param kwargs: post data
        :return: web page
        """
        invoice = transaction.invoice_id
        success = False
        if transaction.state == 'done':
            # Create payment
            success = True
            invoice.pay_muskathlon_invoice()
        elif transaction.state in ('cancel', 'error'):
            # Cancel the invoice and potential registration
            transaction.invoice_id.unlink()
            transaction.registration_id.unlink()

        # clean context and session, then redirect to the confirmation page
        request.session['sale_transaction_id'] = False

        if success:
            return request.render(success_template, kwargs)
        else:
            return request.render(fail_template, kwargs)

    def _prepare_portal_layout_values(self):
        values = super(MuskathlonWebsite, self)._prepare_portal_layout_values()
        registrations = request.env['muskathlon.registration']\
            .search([('partner_id', '=', values['user'].partner_id.id)])
        partner = values['user'].partner_id
        surveys = request.env['survey.user_input']\
            .search([('partner_id', '=', partner.id)])
        surveys_not_started = surveys.filtered(lambda r: r.state == 'new') \
            if surveys else False
        survey_not_started = surveys_not_started[0] \
            if surveys_not_started else False
        surveys_done = surveys.filtered(lambda r: r.state == 'done') \
            if surveys else False
        survey_already_filled = surveys_done[0] \
            if surveys_done else False

        if registrations and partner.ambassador_details_id:
            values['registrations'] = registrations
        elif registrations:
            values['muskathlete_without_ambassador_details'] = True

        values.update({
            'partner': partner,
            'survey_url': request.env.ref(
                'muskathlon.muskathlon_form').public_url,
            'survey_not_started': survey_not_started,
            'survey_already_filled': survey_already_filled,
            'states': request.env['res.country.state'].sudo().search([])
        })
        return values
