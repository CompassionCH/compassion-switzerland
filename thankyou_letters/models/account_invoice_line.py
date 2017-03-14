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

from openerp import models, api, fields


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    event_id = fields.Many2one(
        'crm.event.compassion', compute='_compute_event')

    @api.multi
    def _compute_event(self):
        event_obj = self.env['crm.event.compassion']
        for line in self:
            line.event_id = event_obj.search([
                ('analytic_id', '=', line.account_analytic_id.id)
            ], limit=1)

    @api.multi
    def get_donations(self):
        """
        Gets a dictionary for thank_you communication
        :return: {product_name: total_donation_amount}
        """
        donations = dict()
        event_lines = self.filtered('event_id')
        other_lines = self - event_lines
        events = event_lines.mapped('event_id')

        for event in events:
            total = sum(event_lines.filtered(
                lambda l: l.event_id == event).mapped('price_subtotal'))
            donations[event.name] = "{:,}".format(int(total)).replace(',', "'")

        products = other_lines.mapped('product_id')
        for product in products:
            total = sum(other_lines.filtered(
                lambda l: l.product_id == product).mapped('price_subtotal'))
            donations[product.name] = "{:,}".format(int(total)).replace(
                ',', "'")

        return donations

    @api.multi
    def generate_thank_you(self):
        """
        Creates a thank you letter communication.
        /!\ Must be called only on a single partner and single event at a time.
        """
        comm_obj = self.env['partner.communication.job']
        small = self.env.ref('thankyou_letters.config_thankyou_small')
        standard = self.env.ref('thankyou_letters.config_thankyou_standard')
        large = self.env.ref('thankyou_letters.config_thankyou_large')
        invoice_lines = self

        partner = self.mapped('partner_id')
        partner.ensure_one()
        event = self.mapped('event_id')

        existing_comm = comm_obj.search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ('call', 'pending')),
            ('config_id', 'in', (small + standard + large).ids),
            ('event_id', '=', event.id)
        ])
        if existing_comm:
            invoice_lines += existing_comm.get_objects()

        config = invoice_lines.get_thankyou_config()
        comm_vals = {
            'partner_id': partner.id,
            'config_id': config.id,
            'object_ids': invoice_lines.ids,
            'need_call': config.need_call,
            'event_id': event.id,
        }
        send_mode = config.get_inform_mode(partner)
        comm_vals['send_mode'] = send_mode[0]
        comm_vals['auto_send'] = send_mode[1]
        if partner.is_new_donor:
            comm_vals['send_mode'] = 'physical'

        if existing_comm:
            existing_comm.write(comm_vals)
            existing_comm.refresh_text()
        else:
            # Do not group communications which have not same event linked.
            existing_comm = comm_obj.with_context(
                same_job_search=[('event_id', '=', event.id)]
            ).create(comm_vals)
        self.mapped('invoice_id').write({
            'communication_id': existing_comm.id
        })

    @api.multi
    def get_thankyou_config(self):
        """
        Get how we should thank the selected invoice lines

            - small: < 100 CHF
            - standard: 100 - 999 CHF
            - large: > 1000 CHF or legacy
        :return: partner.communication.config record
        """
        small = self.env.ref('thankyou_letters.config_thankyou_small')
        standard = self.env.ref('thankyou_letters.config_thankyou_standard')
        large = self.env.ref('thankyou_letters.config_thankyou_large')

        # Special case for legacy donation : always treat as large donation
        legacy = 'legacy' in self.with_context(lang='en_US').mapped(
            'product_id.name')

        total_amount = sum(self.mapped('price_subtotal'))
        if total_amount < 100 and not legacy:
            config = small
        elif total_amount < 1000 and not legacy:
            config = standard
        else:
            config = large
        return config
