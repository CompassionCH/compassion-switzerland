# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import mod10r
from odoo.addons.sponsorship_compassion.models.product import \
    GIFT_CATEGORY, SPONSORSHIP_CATEGORY, FUND_CATEGORY


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    invoice_type = fields.Selection([
        ('sponsorship', 'Sponsorship'),
        ('gift', 'Gift'),
        ('fund', 'Fund donation'),
        ('other', 'Other'),
    ], compute='_compute_invoice_type', store=True)

    @api.depends('invoice_line_ids', 'state')
    @api.multi
    def _compute_invoice_type(self):
        for invoice in self.filtered(lambda i: i.state in ('open', 'paid')):
            categories = invoice.with_context(lang='en_US').mapped(
                'invoice_line_ids.product_id.categ_name')
            if SPONSORSHIP_CATEGORY in categories:
                invoice.invoice_type = 'sponsorship'
            elif GIFT_CATEGORY in categories:
                invoice.invoice_type = 'gift'
            elif FUND_CATEGORY in categories:
                invoice.invoice_type = 'fund'
            else:
                invoice.invoice_type = 'other'

    @api.multi
    def action_date_assign(self):
        """Method called when invoice is validated.
            - Add BVR Reference if payment mode is LSV and no reference is
              set.
            - Prevent validating invoices missing related contract.
        """
        for invoice in self.filtered('payment_mode_id'):
            if 'LSV' in invoice.payment_mode_id.name \
                    and not invoice.reference:
                seq = self.env['ir.sequence']
                ref = mod10r(seq.next_by_code('contract.bvr.ref'))
                invoice.write({'reference': ref})
            for invl in invoice.invoice_line_ids:
                if not invl.contract_id and invl.product_id.categ_name in (
                        SPONSORSHIP_CATEGORY, GIFT_CATEGORY):
                    raise UserError(
                        _("Invoice %s for '%s' is missing a sponsorship.") %
                        (str(invoice.id), invoice.partner_id.name))

        return super(AccountInvoice, self).action_date_assign()
