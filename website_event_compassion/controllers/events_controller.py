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
from datetime import datetime

import werkzeug
from dateutil.relativedelta import relativedelta

from odoo import http
from odoo.http import request

from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.cms_form_compassion.controllers.payment_controller import \
    PaymentFormController


class EventsController(PaymentFormController):

    @http.route('/events/', auth='public', website=True)
    def list(self, **kwargs):
        events = request.env['crm.event.compassion'].search([
            ('website_published', '=', True),
        ])
        if len(events) == 1:
            return request.redirect('/event/' + str(events.id))
        return request.render('website_event_compassion.list', {
            'events': events
        })

    ###################################################
    # Methods for the event page and event registration
    ###################################################
    @http.route('/event/<model("crm.event.compassion"):event>/',
                auth='public', website=True)
    def event_page(self, event, **kwargs):
        values = self.get_event_page_values(event, **kwargs)
        registration_form = values['form']
        if registration_form.form_success:
            # The user submitted a registration, redirect to confirmation
            result = werkzeug.utils.redirect(
                registration_form.form_next_url(), code=303)
        else:
            # Display the Event page
            result = request.render(values.pop('website_template'), values)
        return self._form_redirect(result, full_page=True)

    @http.route('/event/<model("event.event"):event>/registration/'
                '<model("event.registration"):registration>/success',
                auth='public', website=True)
    def registration_success(self, event, registration, **kwargs):
        values = {
            'event': event,
            'attendees': registration
        }
        return request.render(
            'website_event_compassion.event_registration_successful',
            values
        )

    def get_event_page_values(self, event, **kwargs):
        """
        Gets the values used by the website to render the event page.
        :param event: crm.event.compassion record to render
        :param kwargs: request arguments
        :return: dict: values for the event website template
                       (must contain event, start_date, end_date, form,
                        main_object and website_template values)
        """
        values = kwargs.copy()
        # This allows the translation to still work on the page
        values.pop('edit_translations', False)
        values.update({
            'event': event,
            'start_date': event.get_date('start_date', 'date_full'),
            'end_date': event.get_date('end_date', 'date_full'),
        })
        registration_form = self.get_form('event.registration', **values)
        registration_form.form_process()
        values.update({
            'form': registration_form,
            'main_object': event,
            'website_template': 'website_event_compassion.event_page',
        })
        return values

    ###################################################
    # Methods for the participant page and the donation
    ###################################################
    @http.route(['/event/<model("crm.event.compassion"):event>'
                 '/<reg_string>-<int:reg_id>',
                 '/event/<model("crm.event.compassion"):event>/<int:reg_id>',
                 ], auth='public', website=True)
    def participant_details(self, event, reg_id, **kwargs):
        """
        :param event: the event record
        :param reg_id: the registration record
        :return:the rendered page
        """
        reg_obj = request.env['event.registration'].sudo()
        registration = reg_obj.browse(reg_id).exists()
        if not registration:
            # This may be an old link. We can fetch the registration
            registration = reg_obj.search([('backup_id', '=', reg_id)])
            if not registration:
                return werkzeug.utils.redirect('/event/' + str(event.id), 301)
        kwargs['form_model_key'] = 'cms.form.event.donation'
        values = self.get_participant_page_values(
            event, registration, **kwargs)
        donation_form = values['form']
        if donation_form.form_success:
            # The user submitted a donation, redirect to confirmation
            result = werkzeug.utils.redirect(
                donation_form.form_next_url(), code=303)
        else:
            result = request.render(values['website_template'], values)
        return self._form_redirect(result)

    def get_participant_page_values(self, event, registration, **kwargs):
        """
        Gets the values used by the website to render the participant page.
        :param event: crm.event.compassion record to render
        :param registration: event.registration record to render
        :param kwargs: request arguments
        :return: dict: values for the event website template
                       (must contain event, start_date, end_date, form,
                        main_object and website_template values)
        """
        values = kwargs.copy()
        # This allows the translation to still work on the page
        values.pop('edit_translations', False)
        values.update({
            'event': event,
            'registration': registration,
        })
        donation_form = self.get_form(False, **values)
        donation_form.form_process()
        values.update({
            'form': donation_form,
            'main_object': registration,
            'website_template': 'website_event_compassion.participant_page',
        })
        return values

    ########################################
    # Methods for after donation redirection
    ########################################
    @http.route('/event/payment/validate',
                type='http', auth="public", website=True)
    def donation_payment_validate(self, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction.
        """
        failure_template = 'website_event_compassion.donation_failure'
        try:
            tx = request.env['payment.transaction'].sudo().\
                _ogone_form_get_tx_from_data(post)
        except ValidationError:
            tx = None

        if not tx or not tx.invoice_id:
            return request.render(failure_template)

        invoice_lines = tx.invoice_id.invoice_line_ids
        event = invoice_lines.mapped('event_id')
        ambassador = invoice_lines.mapped('user_id')
        registration = event.registration_ids.filtered(
            lambda r: r.partner_id == ambassador)
        post.update({
            'registration': registration,
            'event': event
        })
        success_template = self.get_donation_success_template(event)
        return self.compassion_payment_validate(
            tx, success_template, failure_template, **post
        )

    def get_donation_success_template(self, event):
        """
        Gets the website templates for donation confirmation
        :param event: crm.event.compassion record
        :return: xml_id of website template
        """
        return 'website_event_compassion.donation_successful'

    def compassion_payment_validate(
            self, transaction, success_template, fail_template, **kwargs):
        if transaction.state in ('cancel', 'error'):
            # Cancel potential registration(avoid launching jobs at the same
            # time, can cause rollbacks)
            delay = datetime.today() + relativedelta(seconds=10)
            transaction.registration_id.with_delay(eta=delay).\
                cancel_registration()
        return super(EventsController, self).compassion_payment_validate(
            transaction, success_template, fail_template, **kwargs)
