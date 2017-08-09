# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from odoo import api, models, fields


class AccountOperationTemplate(models.Model):

    _inherit = 'account.reconcile.model'

    product_id = fields.Many2one('product.product', 'Product')

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.account_id = self.product_id.property_account_income_id
