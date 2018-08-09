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


class Contract(models.Model):
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
        return super(Contract, self).contract_waiting_mandate()
