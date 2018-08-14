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

from odoo import models, fields, tools

testing = tools.config.get('test_enable')


if not testing:
    class PartnerSmsRegistrationForm(models.AbstractModel):
        _inherit = 'cms.form.recurring.contract'

        # Only propose Direct Debit and Permanent Order
        payment_mode_id = fields.Many2one(
            'account.payment.mode',
            string='Payment mode',
            domain=[('name', 'in', ['LSV', 'Postfinance Direct Debit',
                                    'Permanent Order'])])

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
