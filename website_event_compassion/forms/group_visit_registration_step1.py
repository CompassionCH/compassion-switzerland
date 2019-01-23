# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, tools, _

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests

    class EventRegistrationForm(models.AbstractModel):
        _name = 'cms.form.group.visit.registration'
        _inherit = 'cms.form.event.registration'

        _form_model = 'event.registration'
        _form_model_fields = [
            'name', 'phone', 'email', 'event_id', 'double_room_person',
            'include_flight', 'comments'
        ]
        _form_required_fields = [
            'partner_title', 'partner_lastname', 'partner_firstname',
            'partner_email', 'email_copy', 'partner_birthdate'
        ]
        _display_type = 'full'

        email_copy = fields.Char('Confirm your e-mail address')
        spoken_lang_en = fields.Boolean('English')
        spoken_lang_fr = fields.Boolean('French')
        spoken_lang_de = fields.Boolean('Deutsch')
        spoken_lang_it = fields.Boolean('Italian')
        spoken_lang_es = fields.Boolean('Spanish')
        spoken_lang_po = fields.Boolean('Portuguese')
        include_flight = fields.Boolean(default=True)
        double_room_person = fields.Char('I want to share a double room with:')
        comments = fields.Text(default='')

        @property
        def form_title(self):
            return _("4 steps to register")

        @property
        def form_description(self):
            return _(
                "<p>To live this unique experience of discovery, you just have"
                " to complete the following 4 steps:</p>"
                "<ol>"
                "<li>Register with your coordinates</li>"
                "<li>Accept the travel agreements</li>"
                "<li>Pay a down payment, then the invoice</li>"
                "<li>Prepare the trip</li>"
                "</ol>"
                "<p>Your registration will be validated and a place will be "
                "reserved for you on this trip as soon as you have completed "
                "the first three steps above. "
                "<br/><br/>"
                "I will inform you at each important moment of the preparation"
                " of the trip of the steps to be taken."
                "<br/><br/>"
                "Thank you for your interest in the work of Compassion, "
                "to free more children from extreme poverty every day."
                "<br/><br/>"
                "Rose-Marie Reber"
                "</br>"
                "Head of Tours and Visits at Compassion Suisse"
                "</p>"
            ) + "<br/><br/>"

        @property
        def _form_fieldsets(self):
            lang_fields = []
            if self.env.lang != 'en_US':
                lang_fields.append('spoken_lang_en')
            if self.env.lang != 'fr_CH':
                lang_fields.append('spoken_lang_fr')
            if self.env.lang != 'de_DE':
                lang_fields.append('spoken_lang_de')
            if self.env.lang != 'it_IT':
                lang_fields.append('spoken_lang_it')
            lang_fields.extend([
                'spoken_lang_es', 'spoken_lang_po'])
            event = self.event_id.sudo()
            trip_options = {
                'id': 'trip',
                'title': _('Trip options'),
            }
            if event.flight_price:
                trip_options.update({
                    'description': _(
                        'You can have the flight included (CHF %s) or '
                        'decide to book the flight by yourself if you want '
                        'to extend your trip beyond the dates. '
                        'You can specify someone if you want to share a room '
                        'or leave the field empty to have a single room.'
                    ) % str(int(event.flight_price)),
                    'fields': [
                        'include_flight', 'double_room_person', 'comments']
                })
            else:
                trip_options.update({
                    'description': _(
                        'You can specify someone if you want to share a room '
                        'or leave the field empty to have a single room.'
                    ),
                    'fields': [
                        'double_room_person', 'comments']
                })
            return [
                {
                    'id': 'coordinates',
                    'fields': [
                        'partner_title', 'partner_lastname',
                        'partner_firstname', 'partner_email', 'email_copy',
                        'partner_birthdate', 'partner_phone',
                        'partner_zip', 'partner_city', 'partner_country_id'
                    ]
                },
                {
                    'id': 'language',
                    'title': _('Your spoken languages'),
                    'fields': lang_fields
                },
                trip_options
            ]

        def _form_validate_email_copy(self, value, **req_values):
            if value and value != req_values.get('partner_email'):
                return 'email', _('Verify your e-mail address')
            # No error
            return 0, 0

        def form_before_create_or_update(self, values, extra_values):
            super(EventRegistrationForm, self).form_before_create_or_update(
                values, extra_values
            )
            values.update({
                'stage_id': self.env.ref(
                    'website_event_compassion.stage_group_unconfirmed'
                ).id
            })

        def form_next_url(self, main_object=None):
            return u'/event/{}/confirmation?title={}&message={}'.format(
                self.main_object.compassion_event_id.id,
                _("Thank you!"),
                _("We are glad to confirm your registration to %s. "
                  "You will receive all information for the next steps "
                  "by e-mail.")
                % self.main_object.compassion_event_id.name
            )

        def _get_partner_vals(self, values, extra_values):
            # Add spoken languages
            result = super(EventRegistrationForm,
                           self)._get_partner_vals(values, extra_values)
            spoken_langs = []
            if extra_values.get('spoken_lang_en'):
                spoken_langs.append(
                    self.env.ref(
                        'child_compassion.lang_compassion_english').id
                )
            if extra_values.get('spoken_lang_fr'):
                spoken_langs.append(
                    self.env.ref(
                        'child_compassion.lang_compassion_french').id
                )
            if extra_values.get('spoken_lang_de'):
                spoken_langs.append(
                    self.env.ref(
                        'child_switzerland.lang_compassion_german').id
                )
            if extra_values.get('spoken_lang_it'):
                spoken_langs.append(
                    self.env.ref(
                        'child_switzerland.lang_compassion_italian').id
                )
            if extra_values.get('spoken_lang_es'):
                spoken_langs.append(
                    self.env.ref(
                        'child_compassion.lang_compassion_spanish').id
                )
            if extra_values.get('spoken_lang_po'):
                spoken_langs.append(
                    self.env.ref(
                        'child_compassion.lang_compassion_portuguese').id
                )
            if spoken_langs:
                result['spoken_lang_ids'] = [(4, sid) for sid in spoken_langs]
            return result
