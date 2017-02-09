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
            donations[product.name] = "{:,}".format(total).replace(',', "'")
        return donations

    @api.multi
    def get_thankyou_config(self):
        """
        Get how we should thank the selected invoice lines
        :return: partner.communication.config record
        """
        small = self.env.ref('thankyou_letters.config_thankyou_small')
        standard = self.env.ref('thankyou_letters.config_thankyou_standard')
        large = self.env.ref('thankyou_letters.config_thankyou_large')

        # Special case for legacy donation : always treat as large donation
        legacy = 'legacy' in self.with_context(lang='en_US').mapped(
            'product_id.name')
        total_amount = sum(self.mapped('price_subtotal'))
        if total_amount < 100 and not legacy:
            config = small
        elif total_amount < 1000 and not legacy:
            config = standard
        else:
            config = large
        return config
