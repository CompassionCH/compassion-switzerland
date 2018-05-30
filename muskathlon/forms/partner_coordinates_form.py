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

    class PartnerCoordinatesForm(models.AbstractModel):
        _name = 'cms.form.partner.coordinates'
        _inherit = 'cms.form'

        form_buttons_template = 'muskathlon.modal_form_buttons'
        form_id = 'modal_coordinates'
        _form_model = 'res.partner'
        _form_model_fields = [
            'name', 'email', 'phone', 'street', 'zip',
            'city', 'country_id', 'state_id',
        ]
        _form_required_fields = [
            'name', 'email', 'phone', 'street', 'zip',
            'city', 'country_id',
        ]
        _form_fields_order = [
            'name', 'email', 'phone', 'street', 'zip',
            'city', 'country_id', 'state_id'
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

        def form_before_create_or_update(self, values, extra_values):
            """ Dismiss any pending status message, to avoid multiple
            messages when multiple forms are present on same page.
            """
            self.o_request.website.get_status_message()
