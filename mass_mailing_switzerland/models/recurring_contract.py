# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nathan Fluckiger <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, api


class RecurringContract(models.Model):

    _inherit = 'recurring.contract'

    campaign_id = fields.Many2one('utm.campaign')

    @api.model
    def create(self, vals):
        origin = self.env['recurring.contract.origin'].search([('id', '=', vals['origin_id'])])
        if origin.type == 'event':
            vals['campaign_id'] = origin.event_id.campaign_id.id
        if origin.type == 'marketing':
            analytic = self.env['account.analytic.account'].search([('id', '=', origin.analytic_id.id)])
            analytic.write({'campaign_id': origin.campaign_id.id})

        return super(RecurringContract, self).create(vals)

    @api.multi
    def write(self, vals):
        if 'origin_id' in vals:
            origin = self.env['recurring.contract.origin'].search([('id', '=', vals['origin_id'])])
            if origin.type == 'event':
                vals['campaign_id'] = origin.event_id.campaign_id.id
            if origin.type == 'marketing':
                analytic = self.env['account.analytic.account'].search([('id', '=', origin.analytic_id.id)])
                analytic.write({'campaign_id': origin.campaign_id.id})

        return super(RecurringContract, self).write(vals)


class RecurringContractOrigin(models.Model):

    _inherit = 'recurring.contract.origin'

    campaign_id = fields.Many2one('utm.campaign')
