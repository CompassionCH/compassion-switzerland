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
    @http.route('/events/', auth='public', website=True)
    def list(self, **kw):
        events = http.request.env['crm.event.compassion']
        return http.request.render('muskathlon.list', {
            'events': events.search([]).filtered(
                lambda x: x.muskathlon_event_id),
            # event.year = current_year !
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

    # snippet route for participants_list
    # @http.route('/event-participants/<int:event_id>/', type='json', auth='public', website=True)
    # def participants_list(self, event_id):
    #     participants = http.request.env['muskathlon.registration'].search([('event_id', '=', event_id)])
    #
    #     return http.request.env['ir.ui.view'].render('muskathlon.media_list_template', {
    #         'posts': participants
    #     })
    #
    #     # return http.request.registry['ir.ui.view'].render(http.request.cr, http.request.uid, 'muskathlon.media_list_template', {'posts': participants}, context=http.request.context)
    #
    #     return http.request.render('muskathlon.media_list_template', {
    #         'posts': participants
    #     })
