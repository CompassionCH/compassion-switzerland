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


class RestController(PaymentFormController):

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

    @http.route('/event/<model("crm.event.compassion"):event>/registration',
                auth='public', website=True)
    def event_registration(self, event, **kwargs):
        """
        Displays the registration form of the event
        :return: Rendered template
        """
        values = kwargs.copy()
        # This allows the translation to still work on the page
        values.pop('edit_translations', False)

        ticket = event.odoo_event_id.event_ticket_ids[:1]
        values.update({
            'event': event,
            'start_date': event.get_date('start_date', 'date_full'),
            'end_date': event.get_date('end_date', 'date_full'),
            'ticket': ticket,
            'registration_open': False,
            'registration_not_started': False,
            'registration_closed': False,
            'registration_full': False
        })
        registration_form = self.get_form('event.registration', **values)
        registration_form.form_process()
        if registration_form.form_success:
            # The user submitted a registration, redirect to confirmation
            result = werkzeug.utils.redirect(
                registration_form.form_next_url(), code=303)
        else:
            # Display event registration page
            if ticket:
                available = \
                    ticket.seats_availability == 'unlimited' or \
                    ticket.seats_available > 0
                values.update({
                    'registration_closed': ticket.is_expired,
                    'registration_full': not available,
                    'registration_open': not ticket.is_expired and available

                })
            else:
                values['registration_not_started'] = True
            values.update({
                'form': registration_form,
                'main_object': event,
            })
            result = request.render(
                'website_event_compassion.registration', values)
        return result

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
