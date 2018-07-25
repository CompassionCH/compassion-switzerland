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
from odoo import models, fields


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'
    campaign_id = fields.Many2one('umt.campaign')
    source_id = fields.Many2one('utm.object')
    medium_id = fields.Many2one('utm.medium')
