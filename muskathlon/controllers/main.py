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
import werkzeug

from datetime import datetime
from dateutil.relativedelta import relativedelta
from base64 import b64encode

from odoo.http import request, route
from odoo.addons.website_event_compassion.controllers.events_controller \
    import EventsController
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

    @route(['/event/<model("crm.event.compassion"):event>'
            '/<reg_string>-<int:reg_id>',
            '/event/<model("crm.event.compassion"):event>/<int:reg_id>',
            ],
           auth='public', website=True)
    def participant_details(self, event, reg_id, **kwargs):
        """
        :param event: the event record
        :param reg_id: the registration record
        :return:the rendered page
        """
        reg_obj = request.env['event.registration'].sudo()
        registration = reg_obj.browse(reg_id).exists()
        if not registration:
            # This may be an old link. We can fetch the registration
            registration = reg_obj.search([('backup_id', '=', reg_id)])
            if not registration:
                return werkzeug.utils.redirect('/event/' + str(event.id), 301)
        values = kwargs.copy()
        values.pop('edit_translations', False)
        values.update({
            'event': event,
            'registration': registration,
            'form_model_key': 'cms.form.muskathlon.donation'
        })
        donation_form = self.get_form(False, **values)
        donation_form.form_process()
        if donation_form.form_success:
            # The user submitted a donation, redirect to confirmation
            result = werkzeug.utils.redirect(
                donation_form.form_next_url(), code=303)
        else:
            values.update({
                'form': donation_form,
                'main_object': registration
            })
            result = request.render('muskathlon.participant_details', values)
        return self._form_redirect(result)

    @route(['/my', '/my/home'], type='http', auth="user", website=True)
    def account(self, form_id=None, **kw):
        """ Inject data for forms. """
        values = self._prepare_portal_layout_values()
        partner = values['partner']
        advocate_details_id = partner.advocate_details_id.id

        # Load forms
        kw['form_model_key'] = 'cms.form.muskathlon.trip.information'
        trip_info_form = self.get_form(
            'advocate.details', advocate_details_id, **kw)
        if form_id is None or form_id == trip_info_form.form_id:
            trip_info_form.form_process()

        kw['form_model_key'] = 'cms.form.partner.coordinates'
        coordinates_form = self.get_form('res.partner', partner.id, **kw)
        if form_id is None or form_id == coordinates_form.form_id:
            coordinates_form.form_process()

        kw['form_model_key'] = 'cms.form.advocate.details'
        about_me_form = self.get_form(
            'advocate.details', advocate_details_id, **kw)
        if form_id is None or form_id == about_me_form.form_id:
            about_me_form.form_process()

        values.update({
            'trip_info_form': trip_info_form,
            'coordinates_form': coordinates_form,
            'about_me_form': about_me_form
        })
        result = request.render("website_portal.portal_my_home", values)
        return self._form_redirect(result)

    @route(['/my/api'], type='http', auth='user', website=True)
    def save_ambassador_picture(self, **post):
        user = request.env.user
        partner = user.partner_id
        return_view = 'website_portal.portal_my_home'

        picture = 'picture_1'
        picture_post = post.get(picture)
        if not picture_post:
            picture = 'picture_2'
            picture_post = post.get(picture)

        if picture_post:
            return_view = 'muskathlon.'+picture+'_formatted'
            image_value = b64encode(picture_post.stream.read())
            if not image_value:
                return 'no image uploaded'
            if picture == 'picture_1':
                partner.write({'image': image_value})
            else:
                partner.advocate_details_id.write({
                    'picture_large': image_value
                })

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
        if tx.state == 'done' and not tx.registration_id.lead_id:
            # Create the lead
            tx.registration_id.with_delay().create_muskathlon_lead()
        post.update({'event': event})
        return self.compassion_payment_validate(
            tx, 'muskathlon.new_registration_successful',
            'muskathlon.registration_failure', **post
        )

    @route('/muskathlon_donation/payment/validate',
           type='http', auth="public", website=True)
    def donation_payment_validate(self, **post):
        """ Method that should be called by the server when receiving an update
        for a transaction.
        """
        uid = request.env.ref('muskathlon.user_muskathlon_portal').id
        try:
            tx = request.env['payment.transaction'].sudo(uid).\
                _ogone_form_get_tx_from_data(post)
        except ValidationError:
            tx = None

        if not tx or not tx.invoice_id:
            return request.render('muskathlon.donation_failure')

        invoice_lines = tx.invoice_id.invoice_line_ids
        event = invoice_lines.mapped('event_id')
        ambassador = invoice_lines.mapped('user_id')
        registration = event.registration_ids.filtered(
            lambda r: r.partner_id == ambassador)
        post.update({
            'registration': registration,
            'event': event
        })
        return self.compassion_payment_validate(
            tx, 'muskathlon.donation_successful',
            'muskathlon.donation_failure', **post
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
        # Create lead
        uid = request.env.ref('muskathlon.user_muskathlon_portal').id
        if not registration.sudo(uid).lead_id:
            registration.sudo(uid).with_delay().create_muskathlon_lead()
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

    def _prepare_portal_layout_values(self):
        values = super(MuskathlonWebsite, self)._prepare_portal_layout_values()
        registrations = request.env['event.registration']\
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

        if registrations and partner.advocate_details_id:
            values['registrations'] = registrations
        elif registrations:
            values['muskathlete_without_advocate_details'] = True

        values.update({
            'partner': partner,
            'survey_url': request.env.ref(
                'muskathlon.muskathlon_form').public_url,
            'survey_not_started': survey_not_started,
            'survey_already_filled': survey_already_filled
        })
        return values

    def compassion_payment_validate(
            self, transaction, success_template, fail_template, **kwargs):
        if transaction.state in ('cancel', 'error'):
            # Cancel potential registration(avoid launching jobs at the same
            # time, can cause rollbacks)
            delay = datetime.today() + relativedelta(seconds=10)
            transaction.registration_id.with_delay(eta=delay). \
                delete_muskathlon_registration()
        return super(MuskathlonWebsite, self).compassion_payment_validate(
            transaction, success_template, fail_template, **kwargs)
