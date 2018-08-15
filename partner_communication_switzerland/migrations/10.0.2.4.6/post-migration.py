# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields
from datetime import datetime, timedelta
from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    sponsorships = env['recurring.contract'].search([
        ('activation_date', '!=', None)
    ])
    for sponsorship in sponsorships:
        # if activation date is more than 24h old
        if sponsorship.activation_date <= fields.Datetime.to_string(
                datetime.today() - timedelta(days=1)):
            sponsorship.write({'welcome_active_letter_sent': True})
