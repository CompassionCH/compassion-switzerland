"""
Fichier : payment_method_fee.py
Module : website_sale_postfinance_fee_extension

Rôle :
    Ce fichier étend le modèle Odoo standard 'payment.method' pour y ajouter
    tous les champs de configuration de frais de paiement ('charge_fee',
    'charge_fee_percentage', etc.).

    Ceci est la première étape du déplacement des frais : rendre chaque Méthode
    de Paiement (Gateway : TWINT, Carte) capable de stocker sa propre règle de frais,
    au lieu que le Fournisseur (Provider) stocke la règle unique.

Héritage :
    - payment.method (Modèle de base pour les méthodes de paiement spécifiques)
"""

from odoo import api, fields, models


class PaymentMethod(models.Model):
    _inherit = "payment.method"

    charge_fee = fields.Boolean(
        "Fee charged to customer",
        help="An extra fee line will be added to online order when using this "
             "payment method",
    )
    charge_fee_description = fields.Text(
        "Fee Description", compute="_compute_charge_fee_description"
    )
    charge_fee_product_id = fields.Many2one(
        comodel_name="product.product",
        string="Fee Product",
        domain="[('type', '=', 'service')]"
    )
    charge_fee_fixed_price = fields.Float("Fixed Price", digits="Product Price")
    charge_fee_currency_id = fields.Many2one("res.currency", string="Fee Currency")
    charge_fee_percentage = fields.Float(
        "Percentage", help="Percentage applied to order total"
    )
    charge_fee_type = fields.Selection(
        [("fixed", "Fixed"), ("percentage", "Percentage")],
        string="Computation type",
        default="fixed",
    )

    @api.depends("charge_fee_product_id")
    def _compute_charge_fee_description(self):
        for method in self:
            method.charge_fee_description = (
                method.charge_fee_product_id.name
                if method.charge_fee_product_id
                else None
            )
