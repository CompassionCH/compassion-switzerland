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

    product_id = fields.Many2one('product.product', 'Product', readonly=False)

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
        if product_id and product_id['product_id']:
            product = self.env['product.product'].browse(product_id['product_id'])
            account = product.property_account_income_id
            taxes = product.taxes_id
            res = {}
            if account:
                res['account_id'] = {
                    'id': account.id,
                    'display_name': account.display_name
                }
            else:
                res['account_id'] = False

            if taxes:
                res['tax_id'] = {
                    'id': taxes.id,
                    'display_name': taxes.display_name
                }
            else:
                res['tax_id'] = False
            return res
        return False
