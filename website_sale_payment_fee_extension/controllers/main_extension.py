from odoo import http
from odoo.http import request

from odoo.addons.website_sale_charge_payment_fee.controllers.main import WebsiteSaleFee


class WebsiteSaleFeeExtended(WebsiteSaleFee):
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

        # Try to identify the source of expenses
        if payment_option_id and payment_option_id.isdigit():
            selected_fee_entity = request.env["payment.method"].sudo().browse(
                int(payment_option_id))

            # Retrieves the provider associated with the method
            if selected_fee_entity and selected_fee_entity.provider_ids:
                selected_provider = selected_fee_entity.provider_ids[0]

        # Fallback that uses the Payment Provider if no payment method is found
        if not selected_fee_entity and (
                provider_id or render_values.get("providers_sudo")):

            if provider_id:
                selected_provider = request.env["payment.provider"].sudo().browse(
                    int(provider_id))
            else:
                # Logic for identifying the default provider if not specified.
                providers_sudo = render_values.get("providers_sudo")
                payment_methods_sudo = render_values.get("payment_methods_sudo")
                _selected_provider = [
                    provider_sudo
                    for provider_sudo in payment_methods_sudo.provider_ids
                    if provider_sudo in providers_sudo
                ][:1]
                if len(_selected_provider) > 0:
                    selected_provider = _selected_provider[0]

            # The cost entity becomes the Provider in the event of a fallback.
            selected_fee_entity = selected_provider

        # Application of fees via the designated entity.
        if selected_fee_entity:
            order.sudo().update_fee_line(selected_fee_entity.sudo())
        else:
            order.sudo().update_fee_line(False)

        # Exécution du parent (WebsiteSale) en sautant la logique de l'OCA.
        # This prevents the OCA controller from re-running and overwriting the fees.
        res = super(WebsiteSaleFee, self).shop_payment(**post)

        # Update the rendering context with the selected IDs.
        if payment_option_id:
            res.qcontext["selected_payment_method"] = int(payment_option_id)
        if selected_provider:
            res.qcontext["selected_provider"] = selected_provider
        return res
