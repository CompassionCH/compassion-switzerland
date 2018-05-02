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
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account


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

    @http.route('/my/muskathlons/<int:muskathlon_id>',
                auth='user', website=True)
    def muskathlon_details(self, muskathlon_id):
        reports = request.env['muskathlon.report'].search(
            [('user_id', '=', request.env.user.partner_id.id),
             ('event_id', '=', muskathlon_id)])
        return http.request.render('muskathlon.my_details', {
            'reports': reports
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
            'registration': registration,
            'countries': http.request.env['res.country'].sudo().search([])
        })


class WebsiteAccount(website_account):

    def _prepare_portal_layout_values(self):
        values = super(WebsiteAccount, self)._prepare_portal_layout_values()
        values['registrations'] = request.env['muskathlon.registration']\
            .search([('partner_id', '=', values['user'].partner_id.id)])

        return values
