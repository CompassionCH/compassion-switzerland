from odoo.exceptions import UserError
from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleWithoutState(WebsiteSale):
    # TODO move firstname+name split in partner_compassion module
    # TODO add mobile number in address form otherwise the phone field may stay empty (also in partner_compassion)
    def values_preprocess(self, order, mode, values):
        values["name"] = values["firstname"] + " " + values["lastname"]
        return super().values_preprocess(order, mode, values)

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

    def _get_country_related_render_values(self, kw, render_values):
        """Add contact titles to the render values"""
        res = super()._get_country_related_render_values(kw, render_values)
        res["contact_titles"] = (
            request.env["res.partner.title"]
            .sudo()
            .search([("website_published", "=", True)])
        )
        return res
