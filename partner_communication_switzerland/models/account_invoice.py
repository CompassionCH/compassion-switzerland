# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from collections import OrderedDict

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields

logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    communication_id = fields.Many2one(
        'partner.communication.job', 'Thank you letter', ondelete='set null',
        readonly=True
    )

    @api.model
    def thankyou_summary_cron(self):
        """
        Sends a summary each month of the donations
        :return: True
        """
        comm_obj = self.env['partner.communication.job']
        first = datetime.today().replace(day=1)
        last_month = first - relativedelta(months=1)
        partners = self.env['res.users'].search([
            '|', '|', '|',
            ('name', 'like', 'Maglo Rachel'),
            ('name', 'like', 'Mermod Philippe'),
            ('name', 'like', 'Wulliamoz David'),
        ]).mapped('partner_id')
        invoices = self.search([
            ('type', '=', 'out_invoice'),
            ('invoice_type', '!=', 'sponsorship'),
            ('state', '=', 'paid'),
            ('last_payment', '>=', fields.Date.to_string(last_month)),
            ('last_payment', '<', fields.Date.to_string(first)),
        ])
        config = self.env.ref('thankyou_letters.config_thankyou_summary')
        for partner in partners:
            comm_obj.create({
                'config_id': config.id,
                'partner_id': partner.id,
                'object_ids': invoices.ids
            })
        return True

    @api.multi
    def generate_thank_you(self):
        """
        Creates a thank you letter communication separating events thank you
        and regular thank you.
        """
        partners = self.mapped('partner_id').filtered(
            lambda p: p.thankyou_letter != 'no')
        for partner in partners:
            invoice_lines = self.mapped('invoice_line_ids').filtered(
                lambda l: l.partner_id == partner)
            event_thank = invoice_lines.filtered('event_id')
            other_thank = invoice_lines - event_thank
            for event in event_thank.mapped('event_id'):
                event_thank.filtered(
                    lambda l: l.event_id == event).generate_thank_you()
            if other_thank:
                other_thank.generate_thank_you()

    @api.multi
    def _filter_invoice_to_thank(self):
        """
        Given a recordset of paid invoices, return only those that have
        to be thanked.
        :return: account.invoice recordset
        """
        return self.filtered(
            lambda i: (not i.communication_id or i.communication_id.state in (
                'call', 'pending')) and i.invoice_type != 'sponsorship' and
            (not i.mapped('invoice_line_ids.contract_id') or (
                i.invoice_type == 'gift' and i.origin !=
                'Automatic birthday gift'))
        )
