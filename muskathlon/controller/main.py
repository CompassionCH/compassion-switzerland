# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http


class MuskathlonWebsite(http.Controller):
    @http.route('/events/', auth='user', website=True)
    def list(self, **kw):
        events = http.request.env['crm.event.compassion']
        return http.request.render('muskathlon.list', {
            'events': events.search([]).filtered(
                lambda x: x.muskathlon_event_id)
        })

    @http.route('/event/<model("crm.event.compassion"):event>/',
                auth='public', website=True)
    def details(self, event):
        return http.request.render('muskathlon.details', {
            'event': event
        })

    @http.route('/event/<model("crm.event.compassion"):event>/participant'
                '/<int:partner_id>-<string:partner_name>/', auth='public',
                website=True)
    def participant_details(self, event, partner_id, partner_name):
        """
        :param event: the event record
        :param partner_id: an integer which is the partner_id
        :param partner_name: this field is added only to make the url more
        human. Not used.
        :return:the rendered page
        """
        registration = event.muskathlon_registration_ids.filtered(
            lambda item: item.partner_id.id == partner_id)

        # if partner exist, but is not part of the muskathlon, return 404
        if not registration:
            return http.request.render('website.404')

        return http.request.render('muskathlon.participant_details', {
            'event': event,
            'registration': registration
        })
