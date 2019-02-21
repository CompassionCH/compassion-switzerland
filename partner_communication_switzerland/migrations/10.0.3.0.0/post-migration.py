# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

from dateutil.relativedelta import relativedelta
from openupgradelib import openupgrade
from odoo.fields import Datetime


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Mark old correspondence as opened, to avoid generating thousands
    # of letters to print.
    limit_date = datetime.now() - relativedelta(days=10)
    letters = env['correspondence'].search([
        ('communication_id.send_mode', '=', 'digital'),
        ('communication_id.state', '=', 'done'),
        '|',
        ('partner_id.letter_delivery_preference', '=', 'none'),
        ('sent_date', '<', Datetime.to_string(limit_date))])
    letters.write({
        'email_read': True
    })
