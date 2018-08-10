# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
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
