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
                '/<model("res.partner"):partner>/', auth='public',
                website=True)
    def participant_details(self, event, partner):
        registration = event.muskathlon_registration_ids.filtered(
            lambda item: item.partner_id.id == partner.id)

        # if partner exist, but is not part of the muskathlon, return 404
        if not registration:
            return http.request.render('website.404')

        return http.request.render('muskathlon.participant_details', {
            'event': event,
            'participant': partner,
            'registration': registration
        })
