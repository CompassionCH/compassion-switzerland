from odoo.exceptions import UserError
from odoo.http import request, route

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

    @route("/legal", type="http", auth="public", website=True, sitemap=False)
    def legal_redirect(self):
        legal_link = "https://compassion.ch/protection-des-donnees/"
        if request.env.lang == "de_DE":
            legal_link = "https://compassion.ch/de/datenschutz/"
        if request.env.lang == "it_IT":
            legal_link = "https://compassion.ch/it/privacy-e-termini//"
        return request.redirect(legal_link, code=301)

    def _get_mandatory_fields_billing(self, country_id=False):
        req = super()._get_mandatory_fields_billing(country_id)
        self._filter_mandatory_fields(req)
        return req

    def _get_mandatory_fields_shipping(self, country_id=False):
        req = super()._get_mandatory_fields_shipping(country_id)
        self._filter_mandatory_fields(req)
        return req

    def _filter_mandatory_fields(self, req):
        # Field is removed from view, we can't require it.
        if "state_id" in req:
            req.remove("state_id")
