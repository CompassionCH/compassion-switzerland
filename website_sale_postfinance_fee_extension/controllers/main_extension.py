from odoo import http
from odoo.http import request

from odoo.addons.website_sale_charge_payment_fee.controllers.main import WebsiteSaleFee


class WebsiteSaleFeeExtended(WebsiteSaleFee):
    @http.route(
        "/shop/payment",
        type="http",
        auth="public",
        website=True,
        sitemap=False
    )
    def shop_payment(self, **post):
        order = request.website.sudo().sale_get_order()
        render_values = self._get_shop_payment_values(order, **post)
        provider_id = post.get("provider_id")
        payment_option_id = post.get("payment_option_id")

        selected_provider = False
        selected_fee_entity = False

        # Tente d'identifier la source de frais
        if payment_option_id:
            selected_fee_entity = request.env["payment.method"].sudo().browse(
                int(payment_option_id))

            # Récupère le provider associé à la méthode
            if selected_fee_entity and selected_fee_entity.provider_ids:
                selected_provider = selected_fee_entity.provider_ids[0]

        # Fallback qui utilise le Payment Provider si aucune méthode de paymeent trouvé
        if not selected_fee_entity and (
                provider_id or render_values.get("providers_sudo")):

            if provider_id:
                selected_provider = request.env["payment.provider"].sudo().browse(
                    int(provider_id))
            else:
                # Logique pour identifier le Provider par défaut si non spécifié.
                providers_sudo = render_values.get("providers_sudo")
                payment_methods_sudo = render_values.get("payment_methods_sudo")
                _selected_provider = [
                    provider_sudo
                    for provider_sudo in payment_methods_sudo.provider_ids
                    if provider_sudo in providers_sudo
                ][:1]
                if len(_selected_provider) > 0:
                    selected_provider = _selected_provider[0]

            # L'entité de frais devient le Provider dans le cas du fallback.
            selected_fee_entity = selected_provider

        # Application des frais via l'entité déterminée.
        if selected_fee_entity:
            order.sudo().update_fee_line(selected_fee_entity.sudo())
        else:
            order.sudo().update_fee_line(False)

        # Exécution du parent (WebsiteSale) en sautant la logique de l'OCA.
        # Cela empêche le contrôleur OCA de ré-exécuter et d'écraser les frais.
        res = super(WebsiteSaleFee, self).shop_payment(**post)

        # Mise à jour du contexte de rendu avec les IDs sélectionnés.
        if payment_option_id:
            res.qcontext["selected_payment_method"] = int(payment_option_id)
        if selected_provider:
            res.qcontext["selected_provider"] = selected_provider
        return res
