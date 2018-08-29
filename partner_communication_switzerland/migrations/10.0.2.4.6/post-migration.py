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


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
    update recurring_contract
    set welcome_active_letter_sent=true
    where activation_date <= %s
    """, [fields.Datetime.to_string(datetime.today() - timedelta(days=1))])
