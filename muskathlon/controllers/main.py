# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, _
from odoo.http import request, route
from odoo.addons.website_portal.controllers.main import website_account
from base64 import b64encode


class MuskathlonWebsite(website_account):
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
        events = request.env['crm.event.compassion'].search([
            ('start_date', '>', fields.Date.today()),
            ('muskathlon_event_id', '!=', None)
        ])
        return request.render('muskathlon.details', {
            'event': event,
            'events': events,
            'countries': request.env['res.country'].sudo().search([]),
            'languages': request.env['res.lang'].search([]),

        })

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

        return request.render('muskathlon.participant_details', {
            'event': event,
            'registration': registration,
            'countries': request.env['res.country'].sudo().search([]),
            'acquirers': acquirer_final
        })

    @route(['/my/api'], type='http', auth='user', website=True)
    def save_ambassador_details(self, **post):
        user = request.env.user
        partner = user.partner_id
        return_view = 'website_portal.portal_my_home'
        partner_vals = {}
        details_vals = {}

        if 'type_coordinates' in post:
            partner_vals.update(post)
            partner_vals['zip'] = partner_vals.pop('zipcode')
            return_view = 'muskathlon.coordinates_formatted'

        elif 'type_aboutme' in post:
            details_vals.update(post)
            return_view = 'muskathlon.aboutme_formatted'

        elif 'type_tripinfos' in post:
            details_vals.update(post)
            return_view = 'muskathlon.tripinfos_formatted'

        elif 'type_settings' in post:
            details_vals.update(post)
            details_vals['mail_copy_when_donation'] =\
                'mail_copy_when_donation' in post

        else:
            for picture in ['picture_1', 'picture_2']:
                picture_post = post.get(picture)
                if picture_post:
                    return_view = 'muskathlon.'+picture+'_formatted'
                    image_value = b64encode(picture_post.stream.read())
                    if not image_value:
                        return 'no image uploaded'
                    if picture == 'picture_1':
                        partner_vals['image'] = image_value
                    else:
                        details_vals['picture_large'] = image_value

        if partner_vals:
            partner.write(partner_vals)
        if details_vals:
            partner.ambassador_details_id.write(details_vals)

        values = self._prepare_portal_layout_values()
        return request.render(return_view, values)

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
            'countries': request.env['res.country'].sudo().search([]),
            'states': request.env['res.country.state'].sudo().search([]),
            'tshirt': request.env['ambassador.details'].TSHIRT_SELECTION,
            'ert': request.env['ambassador.details'].ERT_SELECTION,
            'survey_url': request.env.ref(
                'muskathlon.muskathlon_form').public_url,
            'survey_not_started': survey_not_started,
            'survey_already_filled': survey_already_filled
        })
        return values
