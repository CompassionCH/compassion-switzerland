from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleDonation(WebsiteSale):
    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        is_main_address,
        **_kwargs,
    ):
        invalid_fields, missing_fields, error_messages = (
            super()._validate_address_values(
                address_values,
                partner_sudo,
                address_type,
                use_delivery_as_billing,
                required_fields,
                is_main_address,
            )
        )
        try:
            request.env["res.partner"].sudo().check_phone_and_mobile(address_values)
        except UserError as e:
            invalid_fields.add("phone")
            error_messages.append(str(e))
        return invalid_fields, missing_fields, error_messages
