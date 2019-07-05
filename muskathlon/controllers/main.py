# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import json
import urllib
from base64 import b64encode

from odoo.http import request, route
from odoo.addons.website_event_compassion.controllers.events_controller \
    import EventsController
from odoo.addons.cms_form_compassion.tools import validity_checker
from odoo.addons.payment.models.payment_acquirer import ValidationError


class MuskathlonWebsite(EventsController):

    @route('/event/<model("crm.event.compassion"):event>/',
           auth='public', website=True)
    def event_page(self, event, **kwargs):
        result = super(MuskathlonWebsite, self).event_page(event, **kwargs)
        if event.website_muskathlon and result.mimetype == 'application/json':
            # The form is in a modal popup and should be returned in JSON
            # and render in the modal (remove full_page option).
            values = json.loads(result.data)
            values['full_page'] = False
            result.data = json.dumps(values)
        return result

    @route('/my/muskathlon/<model("event.registration"):registration>/'
           'donations',
           auth='user', website=True)
    def my_muskathlon_details(self, registration, **kwargs):
        reports = request.env['muskathlon.report'].search(
            [('user_id', '=', request.env.user.partner_id.id),
             ('event_id', '=', registration.compassion_event_id.id)])
        return request.render('muskathlon.my_details', {
            'reports': reports
        })

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def account(self, form_id=None, **kw):
        """ Inject data for forms. """
        values = self._prepare_portal_layout_values()
        partner = values['partner']
        advocate_details_id = partner.advocate_details_id.id
        registration = partner.registration_ids[:1]
        form_success = False

        # Load forms
        kw['form_model_key'] = 'cms.form.muskathlon.trip.information'
        trip_info_form = self.get_form(
            'event.registration', registration.id, **kw)
        if form_id is None or form_id == trip_info_form.form_id:
            trip_info_form.form_process()
            form_success = trip_info_form.form_success

        kw['form_model_key'] = 'cms.form.partner.coordinates'
        coordinates_form = self.get_form('res.partner', partner.id, **kw)
        if form_id is None or form_id == coordinates_form.form_id:
            coordinates_form.form_process()
            form_success = coordinates_form.form_success

        kw['form_model_key'] = 'cms.form.advocate.details'
        about_me_form = self.get_form(
            'advocate.details', advocate_details_id, **kw)
        if form_id is None or form_id == about_me_form.form_id:
            about_me_form.form_process()
            form_success = about_me_form.form_success

        kw['form_model_key'] = 'cms.form.muskathlon.large.picture'
        large_picture_form = self.get_form(
            'advocate.details', advocate_details_id, **kw)
        if form_id is None or form_id == large_picture_form.form_id:
            large_picture_form.form_process()
            form_success = large_picture_form.form_success

        kw['form_model_key'] = 'cms.form.muskathlon.flight.details'
        kw['registration_id'] = registration.id
        flight_type = kw.get('flight_type')
        kw['flight_type'] = 'outbound'
        flight = registration.flight_ids.filtered(
            lambda f: f.flight_type == 'outbound')
        outbound_flight_form = self.get_form('event.flight', flight.id, **kw)
        if form_id is None or (form_id == outbound_flight_form.form_id and
                               (not flight_type or flight_type == 'outbound')):
            outbound_flight_form.form_process(**kw)
            form_success = outbound_flight_form.form_success
        kw['flight_type'] = 'return'
        flight = registration.flight_ids.filtered(
            lambda f: f.flight_type == 'return')
        return_flight_form = self.get_form('event.flight', flight.id, **kw)
        if form_id is None or (form_id == return_flight_form.form_id and
                               (not flight_type or flight_type == 'return')):
            return_flight_form.form_process(**kw)
            form_success = return_flight_form.form_success

        values.update({
            'trip_info_form': trip_info_form,
            'coordinates_form': coordinates_form,
            'about_me_form': about_me_form,
            'large_picture_form': large_picture_form,
            'outbound_flight_form': outbound_flight_form,
            'return_flight_form': return_flight_form,
        })
        # This fixes an issue that forms fail after first submission
        if form_success:
            result = request.redirect('/my/home')
        else:
            result = request.render("website_portal.portal_my_home", values)
        return self._form_redirect(result, full_page=True)

    @route(['/my/api'], type='http', auth='user', website=True)
    def save_ambassador_picture(self, **post):
        user = request.env.user
        partner = user.partner_id
        return_view = 'website_portal.portal_my_home'
        picture_post = post.get('picture_1')
        if picture_post:
            return_view = 'muskathlon.picture_1_formatted'
            image_value = b64encode(picture_post.stream.read())
            if not image_value:
                return 'no image uploaded'
            partner.write({'image': image_value})
        return request.render(return_view,
                              self._prepare_portal_layout_values())

    @route('/muskathlon_registration/payment/validate',
           type='http', auth="public", website=True)
    def registration_payment_validate(self, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction.
        """
        uid = request.env.ref('muskathlon.user_muskathlon_portal').id
        try:
            tx = request.env['payment.transaction'].sudo(uid).\
                _ogone_form_get_tx_from_data(post)
        except ValidationError:
            tx = None

        if not tx or not tx.registration_id:
            return request.render('muskathlon.registration_failure')

        event = tx.registration_id.compassion_event_id
        if tx.state == 'done' and tx.registration_id:
            # Confirm the registration
            tx.registration_id.confirm_registration()
        post.update({'event': event})
        return self.compassion_payment_validate(
            tx, 'muskathlon.new_registration_successful',
            'muskathlon.registration_failure', **post
        )

    @route('/my/muskathlon/<model("event.registration"):registration>',
           auth="user", website=True)
    def muskathlon_order_material(self, registration, form_id=None, **kw):
        # Load forms
        kw['form_model_key'] = 'cms.form.order.material'
        kw['registration'] = registration
        material_form = self.get_form('crm.lead', **kw)
        if form_id is None or form_id == 'order_material':
            material_form.form_process()

        kw['form_model_key'] = 'cms.form.order.muskathlon.childpack'
        childpack_form = self.get_form('crm.lead', **kw)
        if form_id is None or form_id == 'muskathlon_childpack':
            childpack_form.form_process()

        flyer = '/muskathlon/static/src/img/muskathlon_parrain_example_'
        flyer += request.env.lang[:2] + '.jpg'

        values = {
            'registration': registration,
            'material_form': material_form,
            'childpack_form': childpack_form,
            'flyer_image': flyer
        }
        return request.render(
            "muskathlon.my_muskathlon_order_material", values)

    @route('/muskathlon_registration/'
           '<model("event.registration"):registration>/success',
           type='http', auth="public", website=True)
    def muskathlon_registration_successful(self, registration, **kwargs):
        if validity_checker.is_expired(registration):
            return request.redirect('/events')

        values = {
            'registration': registration,
            'event': registration.compassion_event_id
        }
        return request.render(
            'muskathlon.new_registration_successful_modal', values)

    def get_event_page_values(self, event, **kwargs):
        """
        Gets the values used by the website to render the event page.
        :param event: crm.event.compassion record to render
        :param kwargs: request arguments
        :return: dict: values for the event website template
                       (must contain event, start_date, end_date, form,
                        main_object and website_template values)
        """
        if event.website_muskathlon:
            kwargs['form_model_key'] = 'cms.form.event.registration.muskathlon'
        values = super(MuskathlonWebsite, self).get_event_page_values(
            event, **kwargs)
        if event.website_muskathlon:
            values.update({
                'disciplines': event.sport_discipline_ids.ids,
                'website_template': 'muskathlon.details',
            })
        return values

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
        values = super(MuskathlonWebsite, self).get_participant_page_values(
            event, registration, **kwargs)
        if event.website_muskathlon:
            values['website_template'] = \
                'muskathlon.participant_details'
        return values

    def get_donation_success_template(self, event):
        if event.website_muskathlon:
            return 'muskathlon.donation_successful'
        return super(MuskathlonWebsite,
                     self).get_donation_success_template(event)

    def _prepare_portal_layout_values(self):
        values = super(MuskathlonWebsite, self)._prepare_portal_layout_values()
        registrations = request.env['event.registration']\
            .search([('partner_id', '=', values['user'].partner_id.id)])
        partner = values['user'].partner_id
        surveys = request.env['survey.user_input'].search([
            ('survey_id', 'in', registrations.mapped(
                'event_id.medical_survey_id').ids),
            ('partner_id', '=', partner.id),
        ])
        surveys_not_started = surveys.filtered(lambda r: r.state == 'new') \
            if surveys else False
        survey_not_started = surveys_not_started[0] \
            if surveys_not_started else False
        surveys_done = surveys.filtered(lambda r: r.state == 'done') \
            if surveys else False
        survey_already_filled = surveys_done[0] \
            if surveys_done else False

        child_protection_charter = {
            'has_agreed': partner.has_agreed_child_protection_charter,
            'url': '/partner/%s/child-protection-charter?redirect=%s' %
                   (partner.uuid, urllib.quote('/my/home', safe='')),
        }

        if registrations and partner.advocate_details_id:
            values['registrations'] = registrations
        elif registrations:
            values['muskathlete_without_advocate_details'] = True

        values.update({
            'partner': partner,
            'survey_url': request.env.ref(
                'muskathlon.muskathlon_form').public_url,
            'survey_not_started': survey_not_started,
            'survey_already_filled': survey_already_filled,
            'child_protection_charter': child_protection_charter,
        })
        return values
