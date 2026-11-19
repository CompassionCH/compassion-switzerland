from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _get_aml_default_display_name_list(self):
        # Label the journal items of payment orders with the payment reference
        # (communication of the payment lines) as in v14, for reconciliation.
        if self.payment_order_id and self.payment_reference:
            return [("reference", self.payment_reference)]
        return super()._get_aml_default_display_name_list()
