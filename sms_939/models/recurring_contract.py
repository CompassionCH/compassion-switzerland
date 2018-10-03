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
from odoo import api, models


class RecurringContract(models.Model):
    _inherit = 'recurring.contract'

    @api.multi
    def contract_waiting_mandate(self):
        """
        In case the sponsor paid the first month online, we want to force
        activation of contract and later put it in waiting mandate state.
        """
        for contract in self.filtered('invoice_line_ids'):
            invoices = contract.invoice_line_ids.mapped('invoice_id')
            payment = self.env['account.payment'].search([
                ('invoice_ids', 'in', invoices.ids),
                ('state', '=', 'draft')
            ])
            if payment:
                # Activate contract
                contract._post_payment_first_month()
                contract.contract_active()
        return super(RecurringContract, self).contract_waiting_mandate()

    def associate_group(self, payment_mode_id):
        res = super(RecurringContract, self).associate_group(payment_mode_id)
        self.group_id.on_change_payment_mode()
        return res

    # if self.payment_mode_id.name == "Permanent Order":
    #     computed_ref = self.compute_partner_bvr_ref(
    #         self.partner_id)
    #     if computed_ref:
    #         self.bvr_reference = computed_ref
    #     else:
    #         raise UserError(
    #             _('The reference of the partner has not been set, '
    #               'or is in wrong format. Please make sure to enter a '
    #               'valid BVR reference for the contract.'))
