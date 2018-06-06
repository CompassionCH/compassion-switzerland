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

    class MuskathlonRegistrationForm(models.AbstractModel):
        _name = 'cms.form.muskathlon.registration'
        _inherit = ['cms.form.payment', 'cms.form.match.partner']

        # The form is inside a Muskathlon details page
        form_wrapper_template = 'muskathlon.details'
        form_buttons_template = 'muskathlon.modal_form_buttons'
        form_id = 'modal_muskathlon_registration'
        _form_model = 'muskathlon.registration'
        _form_required_fields = ('sport_level', 'sport_level_description')
        _payment_accept_redirect = '/muskathlon_registration/payment/validate'

        invoice_id = fields.Many2one('account.invoice')

        @property
        def discipline_ids(self):
            return self.event_id.sport_discipline_ids.ids

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'sport',
                    'title': _('Your sport profile'),
                    'description': '',
                    'fields': ['sport_discipline_id', 'sport_level',
                               'sport_level_description',
                               'event_id']
                },
                {
                    'id': 'partner',
                    'title': _('Your coordinates'),
                    'description': '',
                    'fields': [
                        'partner_title',
                        'partner_name', 'partner_email', 'partner_phone',
                        'partner_street', 'partner_zip', 'partner_city',
                        'partner_country_id', 'partner_state_id']
                },
                {
                    'id': 'payment',
                    'title': _('Registration payment'),
                    'description': _(
                        'For validating registrations, we ask a fee of '
                        'CHF 100.- that you can directly pay with your '
                        'Postfinance or Credit Card'
                    ),
                    'fields': ['amount', 'currency_id', 'acquirer_ids']
                },
            ]

        @property
        def form_widgets(self):
            # Hide fields
            res = super(MuskathlonRegistrationForm, self).form_widgets
            res.update({
                'event_id': 'muskathlon.form.widget.hidden',
                'amount': 'muskathlon.form.widget.hidden',
                'currency_id': 'muskathlon.form.widget.hidden',
            })
            return res

        @property
        def _default_currency_id(self):
            # Muskathlon registration payments are in CHF
            return self.env.ref('base.CHF').id

        @property
        def _default_amount(self):
            return 100.0

        @property
        def form_title(self):
            if self.event_id:
                return _("Registration for ") + self.event_id.name
            else:
                return _("New registration")

        @property
        def submit_text(self):
            return _("Proceed with payment")

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
            return req_values.get('event_id', self.event_id.id)

        def form_before_create_or_update(self, values, extra_values):
            """ Create invoice for the registration.
            Create ambassador details.
            """
            super(MuskathlonRegistrationForm,
                  self).form_before_create_or_update(values, extra_values)
            uid = self.env.ref('muskathlon.user_muskathlon_portal').id
            fee_template = self.env.ref('muskathlon.product_registration')
            product = fee_template.sudo(uid).product_variant_ids[:1]
            self.invoice_id = self.env['account.invoice'].sudo(uid).create({
                'partner_id': self.partner_id.id,
                'currency_id': self.currency_id.id,
                'invoice_line_ids': [(0, 0, {
                    'quantity': 1.0,
                    'price_unit': 100,
                    'account_analytic_id': self.event_id.analytic_id.id,
                    'account_id': product.property_account_income_id.id,
                    'name': 'Muskathlon registration fees',
                    'product_id': product.id
                })]
            })
            if not self.partner_id.ambassador_details_id:
                self.partner_id.sudo(uid).ambassador_details_id =\
                    self.env['ambassador.details'].sudo(uid).create({
                        'partner_id': self.partner_id.id
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

        def _edit_transaction_values(self, tx_values):
            """ Add registration link and change reference. """
            tx_values.update({
                'registration_id': self.main_object.id,
                'reference': 'MUSK-REG-' + str(self.main_object.id),
                'invoice_id': self.invoice_id.id
            })
