# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models, fields


class AccountOperationTemplate(models.Model):

    _inherit = 'account.reconcile.model'

    product_id = fields.Many2one('product.product', 'Product')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.account_id = self.product_id.property_account_income_id

    @api.model
    def product_changed(self, product_id):
        """
        Helper to get the account and analytic account in reconcile view.
        :param product_id:
        :return: account_id, analytic_id
        """
        if product_id:
            product = self.env['product.product'].browse(product_id)
            account_id = product.property_account_income_id.id
            analytic_id = self.env['account.analytic.default'].account_get(
                product_id).analytic_id.id
            return {
                'account_id': account_id,
                'analytic_id': analytic_id
            }
        return False
