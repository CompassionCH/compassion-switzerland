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

    class EventDonationForm(models.AbstractModel):
        _name = 'cms.form.event.donation'
        _inherit = ['cms.form.payment', 'cms.form.event.match.partner']

        # The form is inside a Muskathlon participant details page
        form_buttons_template = 'cms_form_compassion.modal_form_buttons'
        form_id = 'modal_donation'
        _payment_accept_redirect = '/event/payment/validate'

        ambassador_id = fields.Many2one('res.partner')
        event_id = fields.Many2one('crm.event.compassion')
        invoice_id = fields.Many2one('account.invoice')

        @property
        def _form_fieldsets(self):
            return [
                {
                    'id': 'payment',
                    'fields': ['amount', 'currency_id', 'acquirer_ids']
                },
                {
                    'id': 'partner',
                    'title': _('Your coordinates'),
                    'description': '',
                    'fields': [
                        'partner_title', 'partner_firstname',
                        'partner_lastname', 'partner_email', 'partner_phone',
                        'partner_street', 'partner_zip', 'partner_city',
                        'partner_country_id']
                },

            ]

        @property
        def form_title(self):
            if self.ambassador_id:
                return _("Donation for ") +\
                    self.ambassador_id.sudo().preferred_name
            else:
                return _("Donation")

        @property
        def submit_text(self):
            return _("Proceed with payment")

        def form_init(self, request, main_object=None, **kw):
            form = super(EventDonationForm, self).form_init(
                request, main_object, **kw)
            # Set default values
            registration = kw.get('registration')
            if registration:
                form.event_id = registration.compassion_event_id
                form.ambassador_id = registration.partner_id
            form.partner_country_id = kw.get(
                'partner_country_id', self.env.ref('base.ch'))
            return form

        def _form_create(self, values):
            """ Manually create account.invoice object """
            product = self.event_id.sudo().odoo_event_id.donation_product_id
            event = self.event_id.sudo()
            ambassador = self.ambassador_id.sudo()
            name = u'[{}] Donation for {}'.format(event.name, ambassador.name)
            self.invoice_id = self.env['account.invoice'].sudo().create({
                'partner_id': self.partner_id.id,
                'currency_id': values['currency_id'],
                'origin': name,
                'invoice_line_ids': [(0, 0, {
                    'quantity': 1.0,
                    'price_unit': values['amount'],
                    'account_id': product.property_account_income_id.id,
                    'name': name,
                    'product_id': product.id,
                    'account_analytic_id': event.analytic_id.id,
                    'user_id': ambassador.id
                })]
            })

        def _edit_transaction_values(self, tx_values):
            """ Add registration link and change reference. """
            tx_values.update({
                'invoice_id': self.invoice_id.id,
                'reference': 'EVENT-DON-' + str(self.invoice_id.id),
            })
