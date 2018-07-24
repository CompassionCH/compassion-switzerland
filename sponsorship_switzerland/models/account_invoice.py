# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015-2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools import mod10r
from odoo.addons.queue_job.job import job, related_action
from odoo.addons.sponsorship_compassion.models.product import \
    GIFT_CATEGORY, SPONSORSHIP_CATEGORY


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    unrec_items = fields.Integer(compute='_compute_unrec_items')

    @api.multi
    def _compute_unrec_items(self):
        move_line_obj = self.env['account.move.line']
        for invoice in self:
            partner = invoice.partner_id
            invoice.unrec_items = move_line_obj.search_count([
                ('partner_id', '=', partner.id),
                ('reconciled', '=', False),
                ('account_id.reconcile', '!=', False),
                ('account_id.code', '=', '1050')
            ])

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

    @api.multi
    def show_transactions(self):
        return self.partner_id.show_lines()

    @api.multi
    def show_move_lines(self):
        account_ids = self.env['account.account'].search(
            [('code', '=', '1050')]).ids
        partner_id = self.partner_id.id
        action = {
            'name': 'Journal Items',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'account.move.line',
            'src_model': 'account.invoice',
            'context': {'search_default_partner_id': [partner_id],
                        'default_partner_id': partner_id,
                        'search_default_unreconciled': 1,
                        'search_default_account_id': account_ids[0]},
        }

        return action

    @job(default_channel='root.group_reconcile')
    @related_action(action='related_action_invoices')
    def group_or_split_reconcile(self):
        """Reconcile given invoices with partner open payments.
        """
        return self._group_or_split_reconcile()
