from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale


class CompassionWebsiteSale(WebsiteSale):
    def _prepare_address_form_values(
        self,
        order_sudo,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        callback="",
        **kwargs,
    ):
        values = super()._prepare_address_form_values(
            order_sudo,
            partner_sudo,
            address_type,
            use_delivery_as_billing,
            callback=callback,
            **kwargs,
        )
        contact_titles = (
            request.env["res.partner.title"]
            .sudo()
            .search(
                [
                    ("is_shown_on_public_forms", "=", True),
                ]
            )
        )
        values["contact_titles"] = contact_titles
        values["show_vat"] = False  # We always hide VAT
        country = values.get("country")
        if not country:
            values["country"] = request.env.ref("base.ch")
        return values

    def _get_mandatory_address_fields(self, country_sudo):
        mandatory_fields = super()._get_mandatory_address_fields(country_sudo)
        mandatory_fields.remove("name")
        mandatory_fields.remove("phone")
        mandatory_fields.add("firstname")
        mandatory_fields.add("lastname")
        return mandatory_fields

    def _get_mandatory_fields(self):
        mandatory_fields = super()._get_mandatory_fields()
        mandatory_fields.remove("name")
        mandatory_fields.remove("phone")
        mandatory_fields.append("firstname")
        mandatory_fields.append("lastname")
        return mandatory_fields

    @route("/legal", type="http", auth="public", website=True, sitemap=False)
    def legal_redirect(self):
        legal_link = "https://compassion.ch/protection-des-donnees/"
        if request.env.lang == "de_DE":
            legal_link = "https://compassion.ch/de/datenschutz/"
        if request.env.lang == "it_IT":
            legal_link = "https://compassion.ch/it/privacy-e-termini//"
        return request.redirect(legal_link, code=301)
