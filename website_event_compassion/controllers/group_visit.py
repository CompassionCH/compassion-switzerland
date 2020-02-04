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

from odoo import http, _
from odoo.http import request

from .events_controller import EventsController


class GroupVisitController(EventsController):
    """
    All the route controllers for group visit registration pages.
    """

    @http.route('/event/<string:reg_uid>/agreements',
                auth='public', website=True)
    def group_visit_step2(self, reg_uid, form_id=None, **kwargs):
        registration = request.env['event.registration'].search([
            ('uuid', '=', reg_uid)])
        if not registration:
            return request.redirect('/events')
        event = registration.compassion_event_id
        values = kwargs.copy()
        values.pop('edit_translations', False)

        values['form_model_key'] = 'cms.form.group.visit.travel.contract'
        contract_form = self.get_form(
            'event.registration', registration.id, **values)
        if form_id is None or 'contract_agreement' in values:
            select_form = 'contract'
            contract_form.form_process()

        values['form_model_key'] = 'cms.form.group.visit.child.protection'
        child_protection_form = self.get_form(
            'event.registration', registration.id, **values)
        if form_id is None or 'final_question' in values:
            select_form = 'child_protection'
            child_protection_form.form_process()

        values['form_model_key'] = 'cms.form.group.visit.trip.form'
        trip_form = self.get_form(
            'event.registration', registration.id, **values)
        if form_id is None or 'emergency_name' in values:
            select_form = 'travel'
            trip_form.form_process()

        values['form_model_key'] = 'cms.form.group.visit.criminal.record'
        criminal_form = self.get_form(
            'event.registration', registration.id, **values)
        if form_id is None or 'criminal_record' in values:
            select_form = 'criminal'
            criminal_form.form_process()

        # Reload registration after form process
        registration.env.clear()
        values.update({
            'event': event,
            'registration': registration,
            'contract_form': contract_form,
            'child_protection_form': child_protection_form,
            'trip_form': trip_form,
            'criminal_form': criminal_form,
            'select': select_form if form_id is not None else form_id,
        })
        if registration.stage_id == request.env.ref(
                'website_event_compassion.stage_group_unconfirmed'):
            return request.render(
                'website_event_compassion.group_visit_step2', values)
        else:
            values = {
                'confirmation_title': _("Thank you!"),
                'confirmation_message': _(
                    "We successfully received all the documents needed for "
                    "the trip. We look forward to sharing with you the work "
                    "of Compassion among poor children in the South."),
                'event': event,
            }
            return request.render(
                'website_event_compassion.event_confirmation_page',
                values)

    @http.route('/event/<string:reg_uid>/down_payment',
                auth='public', website=True)
    def group_visit_down_payment(self, reg_uid, **kwargs):
        kwargs['event_step'] = 3
        return self.get_payment_form(
            reg_uid, 'cms.form.event.down.payment', **kwargs)

    @http.route('/event/<string:reg_uid>/gpv_payment',
                auth='public', website=True)
    def group_visit_payment(self, reg_uid, **kwargs):
        return self.get_payment_form(
            reg_uid, 'cms.form.event.group.visit.payment', **kwargs)

    def get_payment_form(self, reg_uid, form_model, **kwargs):
        kwargs['form_model_key'] = form_model
        values = self._get_group_visit_page_values(
            reg_uid, 'account.invoice', **kwargs)
        if not isinstance(values, dict):
            # values can be a redirect in case of error
            return values
        payment_form = values['form']
        if payment_form.form_success:
            # The user submitted a donation, redirect to confirmation
            return werkzeug.utils.redirect(
                payment_form.form_next_url(), code=303)
        return request.render(
            'website_event_compassion.event_full_page_form', values)

    @http.route('/event/<string:reg_uid>/medical_checklist',
                auth='public', website=True)
    def medical_checklist(self, reg_uid, **kwargs):
        values = self._get_group_visit_page_values(reg_uid, **kwargs)
        if not isinstance(values, dict):
            # values can be a redirect in case of error
            return values
        return request.render(
            'website_event_compassion.group_visit_medical_info', values)

    @http.route('/event/<string:reg_uid>/medical_discharge',
                auth='public', website=True)
    def medical_discharge(self, reg_uid, **kwargs):
        kwargs['form_model_key'] = 'cms.form.group.visit.medical.discharge'
        kwargs['event_step'] = 4
        values = self._get_group_visit_page_values(
            reg_uid, 'event.registration', **kwargs)
        if not isinstance(values, dict):
            # values can be a redirect in case of error
            return values
        return request.render(
            'website_event_compassion.event_full_page_form', values)

    @http.route('/event/<model("crm.event.compassion"):event>/'
                'practical_information',
                auth='public', website=True)
    def group_visit_practical_info(self, event, **kwargs):
        values = kwargs.copy()
        values.pop('edit_translations', False)
        values['event'] = event
        return request.render(
            'website_event_compassion.group_visit_practical_info', values
        )

    @http.route('/event/<string:reg_uid>/meeting_invitation',
                auth='public', website=True)
    def party_invitation(self, reg_uid, **kwargs):
        values = self._get_group_visit_page_values(
            reg_uid, 'event.registration', **kwargs)
        if not isinstance(values, dict):
            # values can be a redirect in case of error
            return values
        # To differentiate the information meeting and the after party
        values['meeting'] = kwargs.get('meeting', 'before_party')
        return request.render(
            'website_event_compassion.group_visit_party_invitation', values)

    @http.route('/event/<string:reg_uid>/after_party',
                auth='public', website=True)
    def after_party(self, reg_uid, **kwargs):
        kwargs['meeting'] = 'after_party'
        return self.party_invitation(reg_uid, **kwargs)

    @http.route('/event/<string:reg_uid>/meeting_confirm',
                auth='public', website=True)
    def meeting_confirm(self, reg_uid, **kwargs):
        values = self._get_group_visit_page_values(
            reg_uid, 'event.registration', **kwargs)
        if not isinstance(values, dict):
            # values can be a redirect in case of error
            return values
        registration = values.get('registration').sudo()
        registration.confirm_registration()
        registration.stage_id = request.env.ref(
            'website_event_compassion.stage_all_confirmed')
        return request.render(
            'website_event_compassion.group_visit_party_confirm', values)

    @http.route('/event/<string:reg_uid>/meeting_decline',
                auth='public', website=True)
    def meeting_decline(self, reg_uid, **kwargs):
        values = self._get_group_visit_page_values(
            reg_uid, 'event.registration', **kwargs)
        if not isinstance(values, dict):
            # values can be a redirect in case of error
            return values
        registration = values.get('registration').sudo()
        registration.button_reg_cancel()
        return request.render(
            'website_event_compassion.group_visit_party_decline', values)

    def _get_group_visit_page_values(self, reg_uid, form_model=None, **kwargs):
        """
        Get the default values for rendering a web page of group visit.
        :param reg_uid: the registration uuid
        :param form_model: optional form model
        :param kwargs: calling args
        :return: dict of values for template rendering
        """
        registration = request.env['event.registration'].search([
            ('uuid', '=', reg_uid)])
        if not registration:
            return request.redirect('/events')
        values = kwargs.copy()
        values.pop('edit_translations', False)
        values.update({
            'registration': registration,
            'event': registration.compassion_event_id
        })
        if form_model is not None:
            form_id = registration.id if \
                form_model == 'event.registration' else None
            form = self.get_form(form_model, form_id, **values)
            form.form_process()
            values['form'] = form
        return values
