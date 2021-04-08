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
        "street",
        "zip",
        "city",
        "country_id",
        "phone",
        "mobile",
        "birthdate_date",
        "email",
    ]
    _form_fields_order = [
        "title",
        "firstname",
        "lastname",
        "street",
        "zip",
        "city",
        "country_id",
        "phone",
        "mobile",
        "email",
        "birthdate_date",
    ]
    _form_required_fields = [
        "title",
        "firstname",
        "lastname",
        "street",
        "zip",
        "city",
        "country_id",
        "email",
    ]

    @property
    def _form_fieldsets(self):
        field_list = self._form_fields_order
        if self.main_object.birthdate_date:
            field_list.pop()
        return [{"id": "coordinates", "fields": field_list}]

    @property
    def form_title(self):
        return _("Coordinates")

    @property
    def submit_text(self):
        return _("Save")

    @property
    def form_msg_success_updated(self):
        return _("Coordinates updated.")

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


class PartnerDeliveryForm(models.AbstractModel):
    _name = "cms.form.partner.delivery"
    _inherit = "cms.form"

    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_delivery"
    _form_model = "res.partner"

    no_physical_letter = fields.Boolean(
        "No postal mail",
        help="Use this option if you don't want to receive any mail by post. "
             "By doing so, you won't receive anymore the photos of your children or "
             "any other postal communication."
    )

    _form_model_fields = [
        "lang",
        "spoken_lang_ids",
        "no_physical_letter"
    ]
    _form_fields_order = [
        "lang",
        "spoken_lang_ids",
        "no_physical_letter",
    ]
    _form_required_fields = [
        "lang"
    ]

    lang = fields.Selection([
        ("fr_CH", "French"),
        ("de_DE", "German"),
        ("it_IT", "Italian"),
        ("en_US", "English"),
    ], string="Primary language",
        help="This will affect the language by which we communicate with you.")
    spoken_lang_ids = fields.Many2many(
        "res.lang.compassion", string="Spoken languages",
        help="This is useful for checking translation needs on your correspondence "
             "with your children.")

    @property
    def form_title(self):
        return _("Communication delivery preferences")

    @property
    def submit_text(self):
        return _("Save")

    @property
    def form_msg_success_updated(self):
        return _("Communication delivery preferences updated.")

    def form_before_create_or_update(self, values, extra_values):
        """ Convert values. """
        partner = self.main_object
        # Avoid changing communication preferences if nothing changed.
        if "no_physical_letter" in values \
                and values["no_physical_letter"] == partner.no_physical_letter:
            del values["no_physical_letter"]
        super().form_before_create_or_update(values, extra_values)
