##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Simon Gonzalez <simon.gonzalez@bluewin.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = "product.product"

    @api.multi
    def recompute_amount(self):
        """ (NOT THE BEST WAY TO HANDLE THE BUTTON APPEARING IN THE SUBVIEW ON PRODUCT.PRODUCT)
        This function is used to calculate the total amount of funds impacted by all the campaigns
        that used a specific product template by summing up the number of invoices paid for each campaign
        that used this product template.
        """
        self.mapped('product_tmpl_id').recompute_amount()
