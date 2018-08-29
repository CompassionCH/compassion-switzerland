# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import models, fields, tools, api

testing = tools.config.get('test_enable')


if not testing:
    class PartnerSmsRegistrationForm(models.AbstractModel):
        _inherit = 'cms.form.recurring.contract'

        # Only propose LSV, Direct Debit and Permanent Order
        payment_mode_id = fields.Many2one(
            'account.payment.mode',
            string='Payment mode',
            domain=lambda self: self._get_domain())

        @api.model
        def _get_domain(self):

            lsv = self.env.ref('sponsorship_switzerland.payment_mode_lsv').ids
            dd = self.env.ref(
                'sponsorship_switzerland.payment_mode_postfinance_dd').ids
            po = self.env.ref(
                'sponsorship_switzerland.payment_mode_permanent_order').ids

            return [('id', 'in', lsv + dd + po)]

        def form_after_create_or_update(self, values, extra_values):
            """
            We should prepare an invoice for LSV/DD
            contract, because invoices are not generated in these cases.
            """
            super(PartnerSmsRegistrationForm,
                  self).form_after_create_or_update(values, extra_values)
            payment_mode_id = values.get('payment_mode_id')
            payment_mode = self.payment_mode_id.sudo().browse(payment_mode_id)
            if 'LSV' in payment_mode or 'Postfinance' in payment_mode:
                delay = datetime.now() + relativedelta(seconds=5)
                self.main_object.sudo().with_delay(
                    eta=delay).create_first_sms_invoice()
