##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nathan Fluckiger <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models


class AccountInvoiceLine(models.Model):
    _inherit = ['account.invoice.line', 'utm.mixin']
    _name = 'account.invoice.line'

    def create(self, vals):
        # Try to link with campaign
        if 'campaign_id' not in vals and (
                'event_id' in vals or 'account_analytic_id' in vals):
            campaign_id = False
            event_id = vals.get('event_id')
            analytic_id = vals.get('account_analytic_id')
            if event_id:
                campaign_id = self.env[
                    'crm.event.compassion'].browse(event_id).campaign_id.id
            if not campaign_id and analytic_id:
                campaign_id = self.env['account.analytic.account']\
                    .browse(analytic_id).campaign_id.id
            vals['campaign_id'] = campaign_id
        return super().create(vals)

    def write(self, vals):
        # Try to link with campaign
        res = super().write(vals)
        if 'event_id' in vals or 'account_analytic_id' in vals:
            for line in self.filtered(lambda l: not l.campaign_id):
                line.campaign_id = line.event_id.campaign_id or \
                    line.account_analytic_id.campaign_id
        return res
