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
import werkzeug

from odoo import http
from odoo.http import request

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
