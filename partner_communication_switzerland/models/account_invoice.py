# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
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

    @api.multi
    def action_invoice_paid(self):
        """ Generate a Thank you Communication when invoice is a donation
            (no sponsorship product inside)
        """
        res = super(AccountInvoice, self).action_invoice_paid()
        invoices = self.filtered(
            lambda i: (not i.communication_id or i.communication_id.state in (
                'call', 'pending')) and i.invoice_type != 'sponsorship' and
            (not i.mapped('invoice_line_ids.contract_id') or (
                i.invoice_type == 'gift' and i.origin !=
                'Automatic birthday gift'))
        )
        if invoices:
            invoices.generate_thank_you()
        return res

    @api.multi
    def write(self, vals):
        """ When invoice is open again, remove it from donation receipt. """
        if vals.get('state') == 'open':
            for invoice in self.filtered(
                    lambda i: i.state == 'paid' and i.communication_id and
                    i.communication_id.state in ('call', 'pending')):
                comm = invoice.communication_id
                object_ids = comm.object_ids
                for line in invoice.invoice_line_ids:
                    object_ids = object_ids.replace(
                        str(line.id), '').replace(',,', '').strip(',')
                if object_ids:
                    # Refresh donation receipt
                    config = self.env['account.invoice.line'].browse(
                        [int(i) for i in object_ids.split(',')]
                    ).get_thankyou_config()
                    send_mode = config.get_inform_mode(comm.partner_id)
                    comm.write({
                        'config_id': config.id,
                        'object_ids': object_ids,
                        'send_mode': send_mode[0],
                        'auto_send': send_mode[1],
                        'need_call': config.need_call,
                    })
                    comm.refresh_text()
                else:
                    comm.unlink()
        return super(AccountInvoice, self).write(vals)

    @api.multi
    def group_by_partner(self):
        """ Returns a dict with {partner_id: invoices}"""
        res = dict()
        for partner in self.mapped('partner_id'):
            res[partner.id] = self.filtered(
                lambda i: i.partner_id == partner)
        return OrderedDict(sorted(
            res.items(), key=lambda t: sum(t[1].mapped('amount_total')),
            reverse=True
        ))

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
