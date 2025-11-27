from odoo import api, fields, models


class SaleOrderFee(models.Model):
    _inherit = "sale.order"

    # Corrige le calcul du total pour inclure le montant des frais
    @api.depends('order_line.price_total', 'amount_payment_fee')
    def _amount_all(self):
        super(SaleOrderFee, self)._amount_all()

        for order in self:
            if order.amount_total is not False and order.amount_payment_fee:
                order.amount_total += order.amount_payment_fee
