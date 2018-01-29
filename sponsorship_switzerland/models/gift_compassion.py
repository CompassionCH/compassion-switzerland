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

from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, models, fields


class Gift(models.Model):
    _inherit = 'sponsorship.gift'

    @api.model
    def process_gifts_cron(self):
        """
        Override to avoid sending LSV/DD gifts too early.
        :return:
        """
        gifts = self.search([
            ('state', '=', 'draft'),
            ('gift_date', '<=', fields.Date.today())
        ])
        lsv_dd_gifts = gifts.filtered(
            lambda g:
            'LSV' in g.sponsorship_id.payment_mode_id.name or
            'Postfinance' in g.sponsorship_id.payment_mode_id.name
        )
        (gifts - lsv_dd_gifts).mapped('message_id').process_messages()
        three_days_limit = date.today() - relativedelta(days=3)
        lsv_dd_gifts.filtered(
            lambda g: fields.Date.from_string(g.gift_date) > three_days_limit
        ).mapped('message_id').process_messages()
        return True
