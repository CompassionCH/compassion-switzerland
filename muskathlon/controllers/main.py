# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http, fields, _
from odoo.http import request
from odoo.addons.website_portal.controllers.main import website_account
from base64 import b64encode


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
    def musk_infos(self, event):
        events = http.request.env['crm.event.compassion'].search([
            ('start_date', '>', fields.Date.today()),
            ('muskathlon_event_id', '!=', None)
        ])
        return http.request.render('muskathlon.details', {
            'event': event,
            'events': events,
            'countries': http.request.env['res.country'].sudo().search([]),
            'languages': http.request.env['res.lang'].search([]),

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
                '/<model("res.partner"):partner>/', auth='public',
                website=True)
    def participant_details(self, event, partner):
        """
        :param event: the event record
        :param partner: a partner record
        :return:the rendered page
        """
        registration = event.muskathlon_registration_ids.filtered(
            lambda item: item.partner_id == partner)

        # if partner exist, but is not part of the muskathlon, return 404
        if not registration:
            return http.request.render('website.404')

        # Fetch the payment acquirers to display a selection with pay button
        # See https://github.com/odoo/odoo/blob/10.0/addons/
        # website_sale/controllers/main.py#L703
        # for reference
        acquirers = request.env['payment.acquirer'].search(
            [('website_published', '=', True)]
        )
        acquirer_final = []
        for acquirer in acquirers:
            acquirer_button = acquirer.with_context(
                submit_class='btn btn-primary',
                submit_txt=_('Pay Now')).sudo().render(
                '/',
                100.0,  # This is a default amount which will be overridden
                request.env.ref('base.CHF').id,
                values={
                    'return_url': '/muskathlon_registration/payment/validate',
                }
            )
            acquirer.button = acquirer_button
            acquirer_final.append(acquirer)

        return http.request.render('muskathlon.participant_details', {
            'event': event,
            'registration': registration,
            'countries': http.request.env['res.country'].sudo().search([]),
            'acquirers': acquirer_final
        })

    @http.route(['/my/api'], type='http', auth='user', website=True)
    def details(self, redirect=None, **post):
        user = request.env.user
        partner = user.partner_id
        vals = {'user': user, 'partner': partner}

        if 'type_coordinates' in post:
            post['zip'] = post.pop('zipcode')
            partner.sudo().write(post)
            return request.render('muskathlon.coordinates_formatted', vals)

        if 'type_aboutme' in post:
            partner.ambassador_details_id.sudo().write(post)
            return request.render('muskathlon.aboutme_formatted', vals)

        if 'type_settings' in post:
            post['mail_copy_when_donation'] = 'mail_copy_when_donation' in post
            partner.ambassador_details_id.sudo().write(post)
            return

        if 'type_tripinfos' in post:
            partner.ambassador_details_id.sudo().write(post)
            return request.render('muskathlon.tripinfos_formatted', vals)

        for picture in ['picture_1', 'picture_2']:
            if picture in post:
                image_value = post[picture].stream.getvalue()
                if not image_value:
                    return 'no image uploaded'
                partner.ambassador_details_id.sudo().write({
                    picture: b64encode(image_value)
                })
                return request.render('muskathlon.'+picture+'_formatted', vals)


class WebsiteAccount(website_account):

    def _prepare_portal_layout_values(self):
        values = super(WebsiteAccount, self)._prepare_portal_layout_values()
        registrations = request.env['muskathlon.registration']\
            .search([('partner_id', '=', values['user'].partner_id.id)])
        partner = values['user'].partner_id
        surveys = request.env['survey.user_input']\
            .search([('partner_id', '=', partner.id)])
        survey_already_filled = surveys\
            .filtered(lambda r: r.state == 'done')[0] if surveys else False

        if registrations and partner.ambassador_details_id:
            values['registrations'] = registrations
        elif registrations:
            values['muskathlete_without_ambassador_details'] = True

        values['partner'] = partner
        values['countries'] = request.env['res.country'].sudo().search([])
        values['states'] = request.env['res.country.state'].sudo().search([])
        values['tshirt'] = request.env['ambassador.details'].TSHIRT_SELECTION
        values['ert'] = request.env['ambassador.details'].ERT_SELECTION
        values['survey_url'] = request.env\
            .ref('muskathlon.muskathlon_form').public_url
        values['survey_already_filled'] = survey_already_filled

        return values
