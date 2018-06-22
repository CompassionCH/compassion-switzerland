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
from odoo.tools import file_open

testing = tools.config.get('test_enable')


if not testing:
    # prevent these forms to be registered when running tests

    class MuskathlonRegistrationForm(models.AbstractModel):
        _name = 'cms.form.muskathlon.registration'
        _inherit = ['cms.form.payment', 'cms.form.match.partner']

        # The form is inside a Muskathlon details page
        form_buttons_template = 'muskathlon.modal_form_buttons'
        form_id = 'modal_muskathlon_registration'
        _form_model = 'muskathlon.registration'
        _form_required_fields = [
            'ambassador_picture_1', 'ambassador_quote', 'sport_level',
            'sport_level_description', 'gtc_accept'
        ]
        _payment_accept_redirect = '/muskathlon_registration/payment/validate'

        invoice_id = fields.Many2one('account.invoice')
        ambassador_picture_1 = fields.Binary('Profile picture')
        ambassador_quote = fields.Text(
            'My motto', default="",
            help="Write a small quote that will appear on your profile page "
                 "and will be used in thank you letters your donors will "
                 "receive."
        )
        gtc_accept = fields.Boolean(
            "Terms and conditions", required=True
        )

        @property
        def discipline_ids(self):
            return self.event_id.sport_discipline_ids.ids

        @property
        def _form_fieldsets(self):
            fieldset = [
                {
                    'id': 'sport',
                    'title': _('Your sport profile'),
                    'description': '',
                    'fields': [
                        'ambassador_picture_1', 'sport_discipline_id',
                        'sport_level', 'sport_level_description',
                        'ambassador_quote', 'event_id'
                    ]
                },
                {
                    'id': 'partner',
                    'title': _('Your coordinates'),
                    'description': '',
                    'fields': [
                        'partner_title',
                        'partner_name', 'partner_email', 'partner_phone',
                        'partner_street', 'partner_zip', 'partner_city',
                        'partner_country_id']
                }
            ]
            if self.event_id.registration_fee:
                fieldset.append({
                    'id': 'payment',
                    'title': _('Registration payment'),
                    'description': _(
                        'For validating registrations, we ask a fee of '
                        'CHF %s that you can directly pay with your '
                        'Postfinance or Credit Card'
                    ) % str(self.event_id.registration_fee),
                    'fields': [
                        'amount', 'currency_id', 'acquirer_ids',
                        'gtc_accept'
                    ]
                })
            else:
                fieldset.append({
                    'id': 'gtc',
                    'fields': ['gtc_accept']
                })
            return fieldset

        @property
        def form_widgets(self):
            # Hide fields
            res = super(MuskathlonRegistrationForm, self).form_widgets
            res.update({
                'event_id': 'muskathlon.form.widget.hidden',
                'amount': 'muskathlon.form.widget.hidden',
                'ambassador_picture_1': 'cms.form.widget.image',
                'gtc_accept': 'muskathlon.form.widget.terms',
            })
            return res

        @property
        def _default_amount(self):
            return self.event_id.registration_fee

        @property
        def form_title(self):
            if self.event_id:
                return _("Registration for ") + self.event_id.name
            else:
                return _("New registration")

        @property
        def submit_text(self):
            if self.event_id.registration_fee:
                return _("Proceed with payment")
            else:
                return _("Register now")

        @property
        def gtc(self):
            html_file = file_open(
                'muskathlon/static/src/html/muskathlon_gtc_{}.html'
                .format(self.env.lang)
            )
            text = html_file.read()
            html_file.close()
            return text

        def form_init(self, request, main_object=None, **kw):
            form = super(MuskathlonRegistrationForm, self).form_init(
                request, main_object, **kw)
            # Set default values
            form.event_id = kw.get('event')
            return form

        def _form_load_sport_level_description(
                self, fname, field, value, **req_values):
            # Default value for muskathlon.registration field
            return req_values.get('sport_level_description', '')

        def _form_load_event_id(
                self, fname, field, value, **req_values):
            # Default value for muskathlon.registration field
            return int(req_values.get('event_id', self.event_id.id))

        def _form_validate_sport_level_description(self, value, **req_values):
            if not re.match(r"^[\w\s'-]+$", value, re.UNICODE):
                return 'sport_level_description', _(
                    'Please avoid any special characters')
            # No error
            return 0, 0

        def form_before_create_or_update(self, values, extra_values):
            """ Create invoice for the registration.
            Create ambassador details.
            """
            super(MuskathlonRegistrationForm,
                  self).form_before_create_or_update(values, extra_values)
            uid = self.env.ref('muskathlon.user_muskathlon_portal').id
            partner = self.partner_id.sudo(uid)
            if self.event_id.registration_fee:
                fee_template = self.env.ref('muskathlon.product_registration')
                product = fee_template.sudo(uid).product_variant_ids[:1]
                invoice_obj = self.env['account.invoice'].sudo(uid)
                self.invoice_id = invoice_obj.create({
                    'partner_id': partner.id,
                    'currency_id': self.currency_id.id,
                    'origin': 'Muskathlon registration',
                    'invoice_line_ids': [(0, 0, {
                        'quantity': 1.0,
                        'price_unit': self.event_id.registration_fee,
                        'account_analytic_id': self.event_id.analytic_id.id,
                        'account_id': product.property_account_income_id.id,
                        'name': 'Muskathlon registration fees',
                        'product_id': product.id
                    })]
                })
            if not partner.ambassador_details_id:
                partner.ambassador_details_id =\
                    self.env['ambassador.details'].sudo(uid).create({
                        'partner_id': partner.id
                    })
            # This field is not needed in muskathlon registration.
            values.pop('partner_name')
            # Force default value instead of setting 0.
            values.pop('amount_objective')
            # Parse integer
            values['event_id'] = int(values['event_id'])

        def _form_create(self, values):
            uid = self.env.ref('muskathlon.user_muskathlon_portal').id
            self.main_object = self.form_model.sudo(uid).create(values.copy())

        def form_next_url(self, main_object=None):
            if self.event_id.registration_fee:
                return super(MuskathlonRegistrationForm, self).form_next_url(
                    main_object)
            else:
                return '/muskathlon_registration/{}/success'.format(
                    self.main_object.id)

        def _edit_transaction_values(self, tx_values):
            """ Add registration link and change reference. """
            tx_values.update({
                'registration_id': self.main_object.id,
                'reference': 'MUSK-REG-' + str(self.main_object.id),
                'invoice_id': self.invoice_id.id
            })
