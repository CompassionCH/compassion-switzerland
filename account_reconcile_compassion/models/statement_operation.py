##############################################################################
#
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import api, models


class AccountOperationTemplate(models.Model):
    _inherit = "account.reconcile.model"

    @api.model
    def product_changed(self, product_id):
        """
        Helper to get the account and analytic account in reconcile view.
        :param product_id:
        :return: account_id, analytic_id
        """
        res = super().product_changed(product_id)
        if product_id:
            analytic_id = (
                self.env["account.analytic.default"]
                .account_get(product_id)
                .analytic_id.id
            )
            res["analytic_id"] = analytic_id
        return res
