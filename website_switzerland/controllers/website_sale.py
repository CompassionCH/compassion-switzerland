from odoo import _
from odoo.http import request

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

    def _validate_address_values(
        self,
        address_values,
        partner_sudo,
        address_type,
        use_delivery_as_billing,
        required_fields,
        is_main_address,
        **kwargs,
    ):
        """The checkout address form edits the partner of the logged-in user in
        place. Odoo guards `name` only, but our form submits firstname and
        lastname, so the identity of a partner that has a user could be
        overwritten by whoever was using the session (T3635). Those fields are
        changed in the account settings instead."""
        invalid_fields, missing_fields, error_messages = (
            super()._validate_address_values(
                address_values,
                partner_sudo,
                address_type,
                use_delivery_as_billing,
                required_fields,
                is_main_address,
                **kwargs,
            )
        )
        if partner_sudo and partner_sudo.with_context(active_test=False).user_ids:
            locked = {
                fname
                for fname in ("firstname", "lastname", "email")
                if fname in address_values
                and (address_values[fname] or "") != (partner_sudo[fname] or "")
            }
            if locked:
                invalid_fields |= locked
                error_messages.append(
                    _(
                        "You cannot change your name or e-mail address while ordering. "
                        "Please do so in your account settings or contact us."
                    )
                )
        return invalid_fields, missing_fields, error_messages
