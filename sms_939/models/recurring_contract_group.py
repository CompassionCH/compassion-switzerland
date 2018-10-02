# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, _
from odoo.exceptions import UserError


class ContractGroup(models.Model):
    _inherit = 'recurring.contract.group'

    @api.multi
    @api.onchange('payment_mode_id')
    def onchange_payment_mode_id(self):
        if self.payment_mode_id.name == "Permanent Order":
            computed_ref = self.compute_partner_bvr_ref(
                self.partner_id)
            if computed_ref:
                self.bvr_reference = computed_ref
            else:
                raise UserError(
                    _('The reference of the partner has not been set, '
                      'or is in wrong format. Please make sure to enter a '
                      'valid BVR reference for the contract.'))
