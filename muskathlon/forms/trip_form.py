# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests

    class MuskathlonDonationForm(models.AbstractModel):
        _name = 'cms.form.muskathlon.trip.information'
        _inherit = 'cms.form'

        form_buttons_template = 'cms_form_compassion.modal_form_buttons'
        form_id = 'modal_tripinfo'
        _form_model = 'ambassador.details'
        _form_required_fields = [
            't_shirt_size', 'emergency_relation_type', 'emergency_name',
            'emergency_phone', 'birth_name', 'passport_number',
            'passport_expiration_date'
        ]

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'tshirt',
                    'fields': ['t_shirt_size']
                },
                {
                    'id': 'emergency',
                    'title': _('Person of contact'),
                    'description': _('Please indicate a contact in case of '
                                     'emergency during the trip.'),
                    'fields': [
                        'emergency_relation_type',
                        'emergency_name', 'emergency_phone'
                    ]
                },
                {
                    'id': 'passport',
                    'title': _('Passport information'),
                    'fields': [
                        'birth_name',
                        'passport_number', 'passport_expiration_date'
                    ]
                },
            ]

        @property
        def form_title(self):
            return _("Personal information for the Muskathlon trip")

        @property
        def submit_text(self):
            return _("Save")

        @property
        def form_msg_success_updated(self):
            return _('Trip information updated.')

        def _form_validate_emergency_phone(self, value, **req_values):
            if not re.match(r'^[+\d][\d\s]{7,}$', value, re.UNICODE):
                return 'emergency_phone', _(
                    'Please enter a valid phone number')
            # No error
            return 0, 0

        def _form_validate_passport_number(self, value, **req_values):
            return self._form_validate_alpha_field('passport_number', value)

        def _form_validate_emergency_name(self, value, **req_values):
            return self._form_validate_alpha_field('emergency_name', value)

        def _form_validate_birth_name(self, value, **req_values):
            return self._form_validate_alpha_field('birth_name', value)

        def _form_validate_passport_expiration_date(self, value, **req_values):
            valid = True
            old = False
            try:
                date = fields.Date.from_string(value)
                today = date.today()
                old = date < today
                valid = not old
            except ValueError:
                valid = False
            finally:
                if not valid:
                    message = _("Please enter a valid date")
                    if old:
                        message = _("Your passport must be renewed!")
                    return 'passport_expiration_date', message
            # No error
            return 0, 0

        def _form_validate_alpha_field(self, field, value):
            if not re.match(r"^[\w\s'-]+$", value, re.UNICODE):
                return field, _('Please avoid any special characters')
            # No error
            return 0, 0

        def form_before_create_or_update(self, values, extra_values):
            """ Dismiss any pending status message, to avoid multiple
            messages when multiple forms are present on same page.
            """
            # Don't remove passport expiration date
            if not values.get('passport_expiration_date', True):
                del values['passport_expiration_date']
            self.o_request.website.get_status_message()
