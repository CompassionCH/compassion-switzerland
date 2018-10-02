# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, tools

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests

    class EventRegistrationForm(models.AbstractModel):
        _name = 'cms.form.event.registration'
        _inherit = 'cms.form.match.partner'

        _form_model = 'event.registration'
        _form_model_fields = [
            'name', 'phone', 'email', 'event_id', 'event_ticket_id',
        ]
        _form_required_fields = ['partner_name', 'partner_email']
        _display_type = 'full'

        event_ticket_id = fields.Many2one('event.event.ticket')
        event_id = fields.Many2one('event.event')

        @property
        def form_msg_success_created(self):
            # No success message as we have a confirmation page
            return False

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'coordinates',
                    'fields': [
                        'partner_name', 'partner_email', 'partner_phone',
                        'partner_zip', 'partner_city'
                    ]
                }
            ]

        def form_init(self, request, main_object=None, **kw):
            form = super(EventRegistrationForm, self).form_init(
                request, main_object, **kw)
            # Set default values
            form.event_id = kw.get('event').odoo_event_id
            form.event_ticket_id = kw.get('ticket')
            return form

        def form_before_create_or_update(self, values, extra_values):
            super(EventRegistrationForm, self).form_before_create_or_update(
                values, extra_values
            )
            values.update({
                'name': extra_values.get('partner_name'),
                'phone': extra_values.get('partner_phone'),
                'email': extra_values.get('partner_email'),
                'event_id': self.event_id.id,
                'event_ticket_id': self.event_ticket_id.id,
            })

        def form_next_url(self, main_object=None):
            return '/event/{}/registration/{}/success'.format(
                self.main_object.event_id.id, self.main_object.id)
