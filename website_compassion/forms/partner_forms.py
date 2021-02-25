##############################################################################
#
#    Copyright (C) 2018-2020 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from datetime import datetime

from odoo import models, fields, _


class PartnerCoordinatesForm(models.AbstractModel):
    _name = "cms.form.partner.my.coordinates"
    _inherit = "cms.form"

    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_my_coordinates"
    _form_model = "res.partner"
    _form_model_fields = [
        "title",
        "firstname",
        "lastname",
        "preferred_name",
        "street",
        "zip",
        "city",
        "country_id",
        "phone",
        "mobile",
        "birthdate_date",
        "email",
        "church_unlinked",
    ]
    _form_fields_order = [
        "title",
        "firstname",
        "lastname",
        "preferred_name",
        "street",
        "zip",
        "city",
        "country_id",
        "phone",
        "mobile",
        "birthdate_date",
        "email",
        "church_unlinked",
    ]

    church_unlinked = fields.Char(string="Church")

    @property
    def form_title(self):
        return _("Coordinates")

    @property
    def submit_text(self):
        return _("Save")

    @property
    def form_msg_success_updated(self):
        return _("Coordinates updated.")

    def _form_load_church_unlinked(self, fname, field, value, **req_values):
        return value or req_values.get(
            fname,
            self.main_object.church_id.name or self.main_object.church_unlinked
        )

    def _form_validate_phone(self, value, **req_values):
        if value and not re.match(r"^[+\d][\d\s]{7,}$", value, re.UNICODE):
            return "phone", _("Please enter a valid phone number")
        # No error
        return 0, 0

    def _form_validate_zip(self, value, **req_values):
        if value and not re.match(r"^\d{3,6}$", value):
            return "zip", _("Please enter a valid zip code")
        # No error
        return 0, 0

    def _form_validate_email(self, value, **req_values):
        if value and not re.match(r"[^@]+@[^@]+\.[^@]+", value):
            return "email", _("Verify your e-mail address")
        # No error
        return 0, 0

    def _form_validate_name(self, value, **req_values):
        return self._form_validate_alpha_field("name", value)

    def _form_validate_street(self, value, **req_values):
        return self._form_validate_alpha_field("street", value, accept=".")

    def _form_validate_city(self, value, **req_values):
        return self._form_validate_alpha_field("city", value, accept="./")

    def _form_validate_alpha_field(self, field, value, accept=""):
        if value and not re.match(fr"^[\w\s'-{accept}]+$", value, re.UNICODE):
            return field, _("Please avoid any special characters")
        # No error
        return 0, 0

    @property
    def form_widgets(self):
        res = super(PartnerCoordinatesForm, self).form_widgets
        res["birthdate_date"] = "cms.form.widget.date.ch"
        return res

    def form_get_widget(self, fname, field, **kw):
        """Retrieve and initialize widget."""
        if fname == "birthdate_date":
            if kw is None:
                kw = {}
            kw["max_date"] = datetime.now().isoformat()
        return self.env[self.form_get_widget_model(fname, field)].widget_init(
            self, fname, field, **kw
        )

    def form_before_create_or_update(self, values, extra_values):
        super().form_before_create_or_update(values, extra_values)
        church = values.get("church_unlinked")
        if church:
            church_record = self.env["res.partner"].search([
                ("is_church", "=", True),
                ("name", "%", church)
            ], limit=1)
            if church_record:
                del values["church_unlinked"]
                values["church_id"] = church_record.id
            else:
                values["church_id"] = False


class PartnerDeliveryForm(models.AbstractModel):
    _name = "cms.form.partner.delivery"
    _inherit = "cms.form"

    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_delivery"
    _form_model = "res.partner"

    global_preference = fields.Selection(
        string="Global communication delivery preference", selection=[
            ("Physical", "Physical"),
            ("Email", "Email"),
        ]
    )

    photo_preference = fields.Selection(
        string="Photo delivery preference", selection=[
            ("Physical", "Physical"),
            ("Email", "Email"),
            ("Email and physical", "Email and physical"),
            ("No", "No"),
        ]
    )

    magazine_preference = fields.Selection(
        string="Magazine delivery preference", selection=[
            ("Physical", "Physical"),
            ("Email", "Email"),
            ("No", "No"),
        ]
    )

    _form_model_fields = [
        "lang",
        "spoken_lang_ids",
        "global_preference",
        "photo_preference",
        "magazine_preference",
        "global_communication_delivery_preference",
        "photo_delivery_preference",
        "nbmag",
    ]
    _form_fields_order = [
        "lang",
        "spoken_lang_ids",
        "global_preference",
        "photo_preference",
        "magazine_preference",
        "global_communication_delivery_preference",
        "photo_delivery_preference",
        "nbmag",
    ]

    def _form_load_global_preference(self, fname, field, value, **req_values):
        if self.main_object.global_communication_delivery_preference == "physical":
            return "Physical"
        else:
            return "Email"

    def _form_load_photo_preference(self, fname, field, value, **req_values):
        if self.main_object.photo_delivery_preference == "none":
            return "No"
        elif self.main_object.photo_delivery_preference == "physical":
            return "Physical"
        elif self.main_object.photo_delivery_preference == "both":
            return "Email and physical"
        else:
            return "Email"

    def _form_load_magazine_preference(self, fname, field, value, **req_values):
        if self.main_object.nbmag == "no_mag":
            return "No"
        elif self.main_object.nbmag == "email":
            return "Email"
        else:
            return "Physical"

    @property
    def form_title(self):
        return _("Communication delivery preferences")

    @property
    def submit_text(self):
        return _("Save")

    @property
    def form_msg_success_updated(self):
        return _("Communication delivery preferences updated.")

    @property
    def form_widgets(self):
        # Hide fields
        res = super().form_widgets
        res["global_communication_delivery_preference"] =\
            "cms_form_compassion.form.widget.hidden"
        res["photo_delivery_preference"] =\
            "cms_form_compassion.form.widget.hidden"
        res["nbmag"] = "cms_form_compassion.form.widget.hidden"
        return res

    def form_extract_values(self, **request_values):
        # We need mappings to go from db to displayed field and vice-versa
        preference_mapping = {
            "Physical": "physical",
            "Email": "digital_only",
            "Email and physical": "both",
            "No": "none",
        }
        magazine_mapping = {
            "Physical": "one",
            "Email": "email",
            "No": "no_mag",
        }
        key_mapping = {
            "global_preference": "global_communication_delivery_preference",
            "photo_preference": "photo_delivery_preference",
            "magazine_preference": "nbmag",
        }

        values = super(PartnerDeliveryForm, self).form_extract_values(
            **request_values
        )
        for form_key in key_mapping.keys():
            if form_key in values and values[form_key]:
                key = key_mapping[form_key]
                # The mapping is different only for the magazines for the value
                if "magazine" in form_key:
                    value = magazine_mapping[values[form_key]]
                else:
                    value = preference_mapping[values[form_key]]
                values[key] = value
            # We don't want those value to go farther as we already used them
            if form_key in values:
                del values[form_key]
        return values
