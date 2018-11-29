# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import http
from odoo.http import request

from .events_controller import EventsController


class GroupVisitController(EventsController):
    """
    All the route controllers for group visit registration pages.
    """

    @http.route('/event/agreements/<string:reg_uid>',
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
        registration.env.invalidate_all()
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
            return request.render(
                'website_event_compassion.group_visit_step2_complete',
                values)
