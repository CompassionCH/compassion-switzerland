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

from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields
from odoo.addons.queue_job.job import job, related_action

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
            '|', '|',
            ('name', 'like', 'Maglo Rachel'),
            ('name', 'like', 'Willi Christian'),
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
        gift_category = self.env.ref(
            'sponsorship_compassion.product_category_gift')
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

        # Send confirmation to ambassadors
        ambassador_config = self.env.ref(
            'partner_communication_switzerland.'
            'ambassador_donation_confirmation_config'
        )
        ambassadors = self.mapped('invoice_line_ids.user_id').filtered(
            'advocate_details_id.mail_copy_when_donation')
        for ambassador in ambassadors:
            # Filter only donations not for made for himself and filter
            # gifts that are thanked but not directly for ambassador.
            ambassador_lines = self.mapped('invoice_line_ids').filtered(
                lambda l: l.user_id == ambassador and
                l.partner_id != ambassador and
                l.product_id.categ_id != gift_category)
            if ambassador_lines:
                self.env['partner.communication.job'].create({
                    'partner_id': ambassador.id,
                    'object_ids': ambassador_lines.ids,
                    'config_id': ambassador_config.id
                })

    @api.multi
    def _filter_invoice_to_thank(self):
        """
        Given a recordset of paid invoices, return only those that have
        to be thanked.
        :return: account.invoice recordset
        """
        return self.filtered(
            lambda i: i.type == 'out_invoice' and (
                not i.communication_id or i.communication_id.state in (
                    'call', 'pending')) and i.invoice_type != 'sponsorship' and
            (not i.mapped('invoice_line_ids.contract_id') or (
                i.invoice_type == 'gift' and i.origin !=
                'Automatic birthday gift'))
        )

    @job(default_channel='root.group_reconcile')
    @related_action(action='related_action_invoices')
    def group_or_split_reconcile(self):
        """Reconcile given invoices with partner open payments.
        """
        super().group_or_split_reconcile()
        # Find if a communication with payment slips is pending and
        # regenerate it.
        jobs = self.env['partner.communication.job'].search([
            ('model', 'in', ['recurring.contract', 'account.invoice']),
            ('state', '!=', 'done'),
            ('partner_id', 'in', self.mapped('partner_id').ids)
        ])
        jobs.refresh_text()

    @api.model
    def cron_send_ambassador_donation_receipt(self):
        """
        Cron for sending the donation receipts to ambassadors
        :return: True
        """
        ambassador_config = self.env.ref(
            'partner_communication_switzerland.'
            'ambassador_donation_confirmation_config'
        )
        jobs = self.env['partner.communication.job'].search([
            ('config_id', '=', ambassador_config.id),
            ('state', '=', 'pending')
        ])
        return jobs.send()
