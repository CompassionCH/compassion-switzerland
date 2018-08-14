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

from odoo import models, tools, _

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests

    class PartnerCoordinatesForm(models.AbstractModel):
        _name = 'cms.form.partner.coordinates'
        _inherit = 'cms.form'

        form_buttons_template = 'cms_form_compassion.modal_form_buttons'
        form_id = 'modal_coordinates'
        _form_model = 'res.partner'
        _form_model_fields = [
            'name', 'email', 'phone', 'street', 'zip',
            'city', 'country_id'
        ]
        _form_required_fields = [
            'name', 'email', 'phone', 'street', 'zip',
            'city', 'country_id',
        ]
        _form_fields_order = [
            'name', 'email', 'phone', 'street', 'zip',
            'city', 'country_id'
        ]

        @property
        def form_title(self):
            return _("Coordinates")

        @property
        def submit_text(self):
            return _("Save")

        @property
        def form_msg_success_updated(self):
            return _('Coordinates updated.')

        def _form_validate_phone(self, value, **req_values):
            if not re.match(r'^[+\d][\d\s]{7,}$', value, re.UNICODE):
                return 'phone', _('Please enter a valid phone number')
            # No error
            return 0, 0

        def _form_validate_zip(self, value, **req_values):
            if not re.match(r'^\d{3,6}$', value):
                return 'zip', _('Please enter a valid zip code')
            # No error
            return 0, 0

        def _form_validate_email(self, value, **req_values):
            if not re.match(r'[^@]+@[^@]+\.[^@]+', value):
                return 'email', _('Verify your e-mail address')
            # No error
            return 0, 0

        def _form_validate_name(self, value, **req_values):
            return self._form_validate_alpha_field('name', value)

        def _form_validate_street(self, value, **req_values):
            return self._form_validate_alpha_field('street', value)

        def _form_validate_city(self, value, **req_values):
            return self._form_validate_alpha_field('city', value)

        def _form_validate_alpha_field(self, field, value):
            if not re.match(r"^[\w\s'-]+$", value, re.UNICODE):
                return field, _('Please avoid any special characters')
            # No error
            return 0, 0

        def form_before_create_or_update(self, values, extra_values):
            """ Dismiss any pending status message, to avoid multiple
            messages when multiple forms are present on same page.
            """
            self.o_request.website.get_status_message()
