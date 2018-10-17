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

from odoo import models, api
from odoo.addons.sponsorship_compassion.models.product import GIFT_CATEGORY


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def get_donations(self):
        """
        Gets a tuple for thank_you communication
        If more than one product, product_name is False
        :return: (total_donation_amount, product_name)
        """
        res_name = False
        total = sum(self.mapped('price_subtotal'))
        total_string = "{:,}".format(int(total)).replace(',', "'")

        event_names = self.mapped('event_id.name')
        product_names = self.mapped('product_id.thanks_name')
        gift = 'gift' in self.mapped('invoice_id.invoice_type')
        if len(event_names) == 1 and not gift:
            res_name = event_names[0]
        elif not event_names and len(product_names) == 1 and not gift:
            res_name = product_names[0]
        # Special case for gifts : mention it's a gift even if several
        # different gifts are made.
        else:
            categories = list(set(self.with_context(lang='en_US').mapped(
                'product_id.categ_name')))
            if len(categories) == 1 and categories[0] == GIFT_CATEGORY:
                gift_template = self.env.ref(
                    'sponsorship_switzerland.product_template_fund_kdo')
                gift = self.env['product.product'].search([
                    ('product_tmpl_id', '=', gift_template.id)
                ], limit=1)
                res_name = gift.thanks_name

        return total_string, res_name

    @api.multi
    def generate_thank_you(self):
        """
        Creates a thank you letter communication.
        Must be called only on a single partner and single event at a time.
        """
        invoice_lines = self.filtered('product_id.requires_thankyou')
        if not invoice_lines:
            # Avoid generating thank you if no valid invoice lines are present
            return

        small = self.env.ref('thankyou_letters.config_thankyou_small') + \
            self.env.ref(
                'partner_communication_switzerland.config_event_small')
        standard = self.env.ref('thankyou_letters.config_thankyou_standard')\
            + self.env.ref('partner_communication_switzerland.'
                           'config_event_standard')
        large = self.env.ref('thankyou_letters.config_thankyou_large') + \
            self.env.ref('partner_communication_switzerland.'
                         'config_event_large')

        partner = invoice_lines.mapped('partner_id')
        partner.ensure_one()
        event = invoice_lines.mapped('event_id')
        ambassadors = invoice_lines.mapped('user_id')

        event_id = event.id

        if invoice_lines.mapped('contract_id'):
            event_id = False

        existing_comm = self.env['partner.communication.job'].search([
            ('partner_id', '=', partner.id),
            ('state', 'in', ('call', 'pending')),
            ('config_id', 'in', (small + standard + large).ids),
            ('event_id', '=', event_id)
        ])
        if existing_comm:
            invoice_lines = existing_comm.get_objects() | invoice_lines

        config = invoice_lines.get_thankyou_config()
        comm_vals = {
            'partner_id': partner.id,
            'config_id': config.id,
            'object_ids': invoice_lines.ids,
            'need_call': config.need_call,
            'event_id': event_id,
            'ambassador_id': len(ambassadors) == 1 and ambassadors.id,
            'print_subject': False,
        }
        send_mode = config.get_inform_mode(partner)
        comm_vals['send_mode'] = send_mode[0]
        comm_vals['auto_send'] = send_mode[1]
        if partner.is_new_donor:
            comm_vals['send_mode'] = 'physical'

        success_stories = invoice_lines.mapped('product_id.success_story_id')
        if success_stories:
            existing_comm = existing_comm.with_context(
                default_success_story_id=success_stories[0].id)

        if existing_comm:
            existing_comm.write(comm_vals)
            existing_comm.refresh_text()
        else:
            # Do not group communications which have not same event linked.
            existing_comm = existing_comm.with_context(
                same_job_search=[('event_id', '=', event_id)]
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
        small_e = self.env.ref('partner_communication_switzerland.'
                               'config_event_small')
        standard = self.env.ref('thankyou_letters.config_thankyou_standard')
        standard_e = self.env.ref('partner_communication_switzerland.'
                                  'config_event_standard')
        large = self.env.ref('thankyou_letters.config_thankyou_large')
        large_e = self.env.ref('partner_communication_switzerland.'
                               'config_event_large')

        # Special case for legacy donation : always treat as large donation
        legacy = 'legacy' in self.with_context(lang='en_US').mapped(
            'product_id.name')
        # Special case for gifts : never put in event donation
        gift = 'gift' in self.mapped('invoice_id.invoice_type')

        total_amount = sum(self.mapped('price_subtotal'))
        event = self.mapped('event_id') and not gift
        if total_amount < 100 and not legacy:
            config = small if not event else small_e
        elif total_amount < 1000 and not legacy:
            config = standard if not event else standard_e
        else:
            config = large if not event else large_e
        return config
