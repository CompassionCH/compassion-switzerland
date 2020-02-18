##############################################################################
#
#    Copyright (C) 2014-2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Cyril Sester, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import mod10r


class ContractGroup(models.Model):
    """ Add BVR on groups and add BVR ref and analytic_id
    in invoices """
    _inherit = 'recurring.contract.group'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    bvr_reference = fields.Char(
        'BVR Ref', size=32, track_visibility="onchange")
    payment_mode_id = fields.Many2one(
        default=lambda self: self._get_op_payment_mode())
    change_method = fields.Selection(default='clean_invoices')

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.model
    def _get_op_payment_mode(self):
        """ Get Permanent Order Payment Term, to set it by default. """
        record = self.env.ref(
            'sponsorship_switzerland.payment_mode_permanent_order')
        return record.id

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.multi
    @api.depends('payment_mode_id', 'bvr_reference', 'partner_id')
    def name_get(self):
        res = list()
        for gr in self:
            name = ''
            if gr.payment_mode_id:
                name = gr.payment_mode_id.name
            if gr.bvr_reference:
                name += ' ' + gr.bvr_reference
            if name == '':
                name = gr.partner_id.name + ' ' + str(gr.id)
            res.append((gr.id, name))
        return res

    @api.multi
    def write(self, vals):
        """ If sponsor changes his payment term to LSV or DD,
        change the state of related contracts so that we wait
        for a valid mandate before generating new invoices.
        """
        contracts = self.env['recurring.contract']
        inv_vals = dict()
        if 'payment_mode_id' in vals:
            inv_vals['payment_mode_id'] = vals['payment_mode_id']
            payment_mode = self.env['account.payment.mode'].with_context(
                lang='en_US').browse(vals['payment_mode_id'])
            payment_name = payment_mode.name
            contracts |= self.mapped('contract_ids')
            for group in self:
                old_term = group.payment_mode_id.name
                if 'LSV' in payment_name or 'Postfinance' in payment_name:
                    group.contract_ids.contract_waiting_mandate()
                    # LSV/DD Contracts need no reference
                    if group.bvr_reference and \
                            'multi-months' not in payment_name:
                        vals['bvr_reference'] = False
                elif 'LSV' in old_term or 'Postfinance' in old_term:
                    group.contract_ids.contract_active()
        if 'bvr_reference' in vals:
            inv_vals['reference'] = vals['bvr_reference']
            contracts |= self.mapped('contract_ids')

        res = super().write(vals)

        if contracts:
            # Update related open invoices to reflect the changes
            inv_lines = self.env['account.invoice.line'].search([
                ('contract_id', 'in', contracts.ids),
                ('state', 'not in', ('paid', 'cancel'))])
            invoices = inv_lines.mapped('invoice_id')
            invoices.action_invoice_cancel()
            invoices.action_invoice_draft()
            # invoices.env.invalidate_all()
            invoices.env.clear()
            invoices.write(inv_vals)
            invoices.action_invoice_open()
        return res

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def compute_partner_bvr_ref(self, partner=None, is_lsv=False):
        """ Generates a new BVR Reference.
        See file /nas/it/devel/Code_ref_BVR.xls for more information."""
        self.ensure_one()
        if self.exists():
            # If group was already existing, retrieve any existing reference
            ref = self.bvr_reference
            if ref:
                return ref
        partner = partner or self.partner_id
        result = '0' * (9 + (7 - len(partner.ref))) + partner.ref
        count_groups = str(self.search_count(
            [('partner_id', '=', partner.id)]))
        result += '0' * (5 - len(count_groups)) + count_groups
        # Type '0' = Sponsorship
        result += '0'
        result += '0' * 4

        if is_lsv:
            result = '004874969' + result[9:]
        if len(result) == 26:
            return mod10r(result)

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.onchange('partner_id')
    def on_change_partner_id(self):
        if not self.partner_id:
            self.bvr_reference = False
            return

        partner = self.partner_id
        if partner.ref:
            computed_ref = self.compute_partner_bvr_ref(partner)
            if computed_ref:
                self.bvr_reference = computed_ref
            else:
                raise UserError(
                    _('The reference of the partner has not been set, '
                      'or is in wrong format. Please make sure to enter a '
                      'valid BVR reference for the contract.'))

    @api.onchange('payment_mode_id')
    def on_change_payment_mode(self):
        """ Generate new bvr_reference if payment term is Permanent Order
        or BVR """
        payment_mode_id = self.payment_mode_id.id
        pmobj = self.env['account.payment.mode'].with_context(
            lang='en_US')
        need_bvr_ref_term_ids = pmobj.search([
            '|', ('name', 'in', ('Permanent Order', 'BVR')),
            ('name', 'like', 'multi-months')]).ids
        lsv_term_ids = pmobj.search(
            [('name', 'like', 'LSV')]).ids
        if payment_mode_id in need_bvr_ref_term_ids:
            is_lsv = payment_mode_id in lsv_term_ids
            partner = self.partner_id
            if partner.ref and (not self.bvr_reference or is_lsv):
                self.bvr_reference = self.compute_partner_bvr_ref(
                    partner, is_lsv)
        else:
            self.bvr_reference = False

    @api.onchange('bvr_reference')
    def on_change_bvr_ref(self):
        """ Test the validity of a reference number. """
        bvr_reference = self.bvr_reference
        is_valid = bvr_reference and bvr_reference.isdigit()
        if is_valid and len(bvr_reference) == 26:
            bvr_reference = mod10r(bvr_reference)
        elif is_valid and len(bvr_reference) == 27:
            valid_ref = mod10r(bvr_reference[:-1])
            is_valid = (valid_ref == bvr_reference)
        else:
            is_valid = False

        if is_valid:
            self.bvr_reference = bvr_reference
        elif bvr_reference:
            raise UserError(
                _('The reference of the partner has not been set, or is in '
                  'wrong format. Please make sure to enter a valid BVR '
                  'reference for the contract.'))

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _setup_inv_data(self, journal, invoicer, contracts):
        """ Inherit to add BVR ref and mandate """
        inv_data = super()._setup_inv_data(
            journal, invoicer, contracts)

        ref = ''
        bank_modes = self.env['account.payment.mode'].with_context(
            lang='en_US').search(
            ['|', ('name', 'like', 'LSV'), ('name', 'like', 'Postfinance')])
        bank = self.env['res.partner.bank']
        if self.bvr_reference:
            ref = self.bvr_reference
            bank = bank.search([('acc_number', '=', '01444437')])
        elif self.payment_mode_id in bank_modes:
            seq = self.env['ir.sequence']
            ref = mod10r(seq.next_by_code('contract.bvr.ref'))
            bank = self.payment_mode_id.fixed_journal_id.bank_account_id
        mandate = self.env['account.banking.mandate'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'valid')
        ], limit=1)
        inv_data.update({
            'reference': ref,
            'mandate_id': mandate.id,
            'partner_bank_id': bank.id,
        })

        return inv_data

    def _get_gen_states(self):
        return ['waiting', 'active']
