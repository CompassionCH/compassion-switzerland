from odoo.exceptions import UserError
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleWithoutState(WebsiteSale):
    def values_preprocess(self, order, mode, values):
        values["name"] = values["firstname"] + " " + values["lastname"]
        return super().values_preprocess(order, mode, values)

    def checkout_form_validate(self, mode, all_form_values, data):
        error, error_message = super().checkout_form_validate(
            mode, all_form_values, data
        )
        try:
            request.env["res.partner"].check_phone_and_mobile(data)
        except UserError as exc:
            error["phone"] = "error"
            error_message.append(exc.args[0])
        return error, error_message
