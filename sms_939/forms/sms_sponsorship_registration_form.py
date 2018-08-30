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
