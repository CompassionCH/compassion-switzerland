"""
Fichier : main_extension.py
Module : website_sale_postfinance_fee_extension (Votre module d'extension)

Rôle :
    Surcharge la route Odoo de paiement (/shop/payment) pour modifier la logique
    d'application des frais de paiement (payment fees) définis par le module OCA.

    Objectif : Prioriser le 'payment.method' (Méthode spécifique : TWINT, Carte)
    comme source de frais au lieu du payment.provider (provider général : PostFinance).

    Fallback : Assure que le calcul des frais fonctionne même pour les
    fournisseurs qui n'utilisent PAS de méthodes spécifiques (ex: Virement Bancaire)
    ou en cas d'erreur/absence de la sélection de méthode.
"""

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleFeeExtended(WebsiteSale):
    @http.route(
        "/shop/payment", type="http", auth="public", website=True, sitemap=False
    )
    def shop_payment(self, **post):
        order = request.website.sudo().sale_get_order()
        render_values = self._get_shop_payment_values(order, **post)
        provider_id = post.get("provider_id")
        payment_option_id = post.get("payment_option_id")

        selected_provider = False
        selected_fee_entity = False

        if payment_option_id:
            selected_fee_entity = request.env["payment.method"].sudo().browse(
                int(payment_option_id))

            if selected_fee_entity and selected_fee_entity.provider_ids:
                selected_provider = selected_fee_entity.provider_ids[0]

        # Fallback qui utiliser le Payment Provider
        # Cette logique s'active si aucune méthode spécifique (payment_option_id)
        # n'a été sélectionnée. Cela couvre les fournisseurs standard
        # (sans méthode PostFinance) qui ne sont identifiés que par provider_id.
        if not selected_fee_entity and (
                provider_id or render_values.get("providers_sudo")):
            if provider_id:
                selected_provider = request.env["payment.provider"].sudo().browse(
                    int(provider_id))
            else:
                providers_sudo = render_values.get("providers_sudo")
                payment_methods_sudo = render_values.get("payment_methods_sudo")
                _selected_provider = [
                    provider_sudo
                    for provider_sudo in payment_methods_sudo.provider_ids
                    if provider_sudo in providers_sudo
                ][:1]
                if len(_selected_provider) > 0:
                    selected_provider = _selected_provider[0]

            selected_fee_entity = selected_provider

        # Calcul des frais
        if selected_fee_entity:
            order.sudo().update_fee_line(selected_fee_entity.sudo())

        res = super().shop_payment(**post)
        if payment_option_id:
            res.qcontext["selected_payment_method"] = int(payment_option_id)
        if selected_provider:
            res.qcontext["selected_provider"] = selected_provider
        return res
