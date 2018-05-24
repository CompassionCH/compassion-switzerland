# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, tools, _

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests

    class MuskathlonDonationForm(models.AbstractModel):
        _name = 'cms.form.muskathlon.trip.information'
        _inherit = 'cms.form'

        form_buttons_template = 'muskathlon.modal_form_buttons'
        form_id = 'modal_tripinfo'
        _form_model = 'ambassador.details'
        _form_required_fields = [
            'tshirt_size', 'emergency_relation_type', 'emergency_name',
            'emergency_phone', 'birth_name', 'passport_number',
            'passport_expiration_date'
        ]

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'tshirt',
                    'fields': ['tshirt_size']
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

        def form_before_create_or_update(self, values, extra_values):
            """ Dismiss any pending status message, to avoid multiple
            messages when multiple forms are present on same page.
            """
            # Don't remove passport expiration date
            if not values.get('passport_expiration_date', True):
                del values['passport_expiration_date']
            self.o_request.website.get_status_message()
