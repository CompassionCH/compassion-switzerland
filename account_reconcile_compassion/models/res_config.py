# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Marco Monzione <marco.mon@windowslive.com>, Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, fields, api


class AccountConfigSettings(models.TransientModel):
    """
    Add the possibility to configure a default analytic account in
    acconting->setings to be use for file upload when there is
    currency exchange.
    """

    _inherit = 'account.config.settings'

    currency_exchange_analytic_account = fields.Many2one(
        'account.analytic.account',
        default=lambda s: s.get_currency_exchange_analytic_account()
    )

    @api.multi
    def set_currency_exchange_analytic_account(self):
        ir_config = self.env['ir.config_parameter']
        ir_config.set_param(
            'account_reconcile_compassion.currency_exchange_analytic_account',
            self.currency_exchange_analytic_account.id
        )
        return True

    def get_currency_exchange_analytic_account(self):

        analytic_account_id = self.env['ir.config_parameter'].get_param(
            'account_reconcile_compassion.currency_exchange_analytic_account'
        )
        analytic_account = self.env['account.analytic.account'].search([
            ('id', '=', analytic_account_id)
        ])
        return analytic_account
