# -*- encoding: utf-8 -*-
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

from openerp import api, models, fields

logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    communication_id = fields.Many2one(
        'partner.communication.job', 'Thank you letter', ondelete='set null',
        readonly=True
    )

    @api.multi
    def confirm_paid(self):
        """ Generate a Thank you Communication when invoice is a donation
            (no sponsorship product inside)
        """
        res = super(AccountInvoice, self).confirm_paid()
        invoices = self.filtered(
            lambda i: (
                not i.communication_id or
                i.communication_id.state in ('call', 'pending'))
            and "Sponsorship" not in i.mapped(
                'invoice_line.product_id.categ_name')
        )
        if invoices:
            invoices._generate_thank_you()
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
                for line in invoice.invoice_line:
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

    def _generate_thank_you(self):
        """
        Creates a thank you letter communication separating events thank you
        and regular thank you.
        """
        partners = self.mapped('partner_id')
        for partner in partners:
            invoice_lines = self.mapped('invoice_line').filtered(
                lambda l: l.partner_id == partner)
            event_thank = invoice_lines.filtered('event_id')
            other_thank = invoice_lines - event_thank
            for event in event_thank.mapped('event_id'):
                event_thank.filtered(
                    lambda l: l.event_id == event).generate_thank_you()
            if other_thank:
                other_thank.generate_thank_you()
