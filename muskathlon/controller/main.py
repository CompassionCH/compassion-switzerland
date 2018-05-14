# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import http, fields
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

    @http.route('/muskathlon_registration/event/<model('
                '"crm.event.compassion"):event>/',
                auth='public', website=True, methods=['GET'])
    @http.route('/muskathlon_registration/', defaults={'event': None},
                auth='public', website=True, methods=['GET'])
    def new_registration(self, event):
        events = http.request.env['crm.event.compassion'].search([
            ('start_date', '>', fields.Date.today()),
            ('muskathlon_event_id', '!=', None)
        ])
        return http.request.render('muskathlon.new_registration', {
            'event': event,
            'events': events,
            'sports': request.env['sport.discipline'].sudo().search([]),
            'countries': request.env['res.country'].sudo().search([]),
            'states': request.env['res.country.state'].sudo().search([]),
            'tshirt': request.env['ambassador.details'].TSHIRT_SELECTION,
            'ert': request.env['ambassador.details'].ERT_SELECTION,
            'languages': request.env['res.lang'].search([]),

        })

    @http.route('/muskathlon_registration/event/<model('
                '"crm.event.compassion"):event>/',
                auth='public', website=True, methods=['POST'])
    @http.route('/muskathlon_registration/', defaults={'event': None},
                auth='public', website=True, methods=['POST'])
    def receive_form_registration(self, event, **post):
        # find partner
        partner = http.request.env['res.partner'].search([
            ('email', '=ilike', post['email'])], limit=1)
        country_id = http.request.env['res.country'].search([(
            'code', '=', post['OWNERCTY'])]).id
        if not partner:
            partner = http.request.env['res.partner'].search([
                ('lastname', '=ilike', post['lastname']),
                ('firstname', '=ilike', post['firstname']),
                ('zip', '=', post['zip'])], limit=1)
        if not partner:
            # no match found -> creating a new one.
            partner = http.request.env['res.partner'].create({
                'firstname': post['firstname'],
                'lastname': post['lastname'],
                'email': post['email'],
                'phone': post['tel'],
                'street': post['street'],
                'city': post['town'],
                'zip': post['zip'],
                'country_id': country_id
            })

        sport = request.env['sport.discipline'].browse(post['sport_id'])
        event = request.env['crm.event.compassion'].browse(post['event_id'])
        registration = request.env['muskathlon.registration'].create({
            'event_id': event.id,
            'partner_id': partner.id,
            'sport_discipline_id': sport.id
        })
        request.env['ambassador.details'].sudo().create({
            'description': post['description'],
            'picture_1': b64encode(post['picture_1'].stream.getvalue()),
            'picture_2': b64encode(post['picture_2'].stream.getvalue()),
        })

        # TODO
        # Ajouter un booléan registration_open pour afficher ou non le bouton
        #  d'inscription sur la page web de l'event
        # TODO add picture_1, picture_2, motivation, description, to the
        # ambassador details
        # TODO Create a Lead in odoo + notifier
        # TODO payment 100chf (could be done in a second step)

        if registration:
            return http.request.render(
                'muskathlon.new_registration_successful', {
                    'event': event
                })
        # TODO do something is the registration is unsuccessful

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
        values['registrations'] = request.env['muskathlon.registration']\
            .search([('partner_id', '=', values['user'].partner_id.id)])

        values['partner'] = values['user'].partner_id
        values['countries'] = request.env['res.country'].sudo().search([])
        values['states'] = request.env['res.country.state'].sudo().search([])
        values['tshirt'] = request.env['ambassador.details'].TSHIRT_SELECTION
        values['ert'] = request.env['ambassador.details'].ERT_SELECTION

        return values
