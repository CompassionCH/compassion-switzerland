# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from openerp import models, api


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.multi
    def get_donations(self):
        """
        Gets a dictionary for thank_you communication
        :return: {product_name: total_donation_amount}
        """
        donations = dict()
        products = self.mapped('product_id')
        for product in products:
            total = sum(self.filtered(
                lambda l: l.product_id == product).mapped('price_subtotal'))
            donations[product.name] = "{:.2f,}".format(total).replace(',', "'")
        return donations
