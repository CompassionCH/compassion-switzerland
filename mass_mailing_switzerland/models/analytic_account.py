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


class AnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    campaign_id = fields.Many2one("utm.campaign", readonly=False)


class AnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    state = fields.Selection(related='move_id.invoice_id.state', readonly=True)
