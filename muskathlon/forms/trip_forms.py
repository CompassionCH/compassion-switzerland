##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import pytz
import re

from datetime import datetime
from odoo import models, fields, _


class MuskathlonTripForm(models.AbstractModel):
    _name = "cms.form.muskathlon.trip.information"
    _inherit = "cms.form"

    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_tripinfo"
    _form_model = "event.registration"
    _form_model_fields = [
        "t_shirt_size",
        "emergency_relation_type",
        "emergency_name",
        "emergency_phone",
        "birth_name",
        "passport_number",
        "passport_expiration_date",
    ]
    _form_required_fields = [
        "t_shirt_size",
        "emergency_relation_type",
        "emergency_name",
        "emergency_phone",
        "birth_name",
        "passport_number",
        "passport_expiration_date",
    ]

    @property
    def _form_fieldsets(self):
        return [
            {"id": "tshirt", "fields": ["t_shirt_size"]},
            {
                "id": "emergency",
                "title": _("Person of contact"),
                "description": _(
                    "Please indicate a contact in case of "
                    "emergency during the trip."
                ),
                "fields": [
                    "emergency_relation_type",
                    "emergency_name",
                    "emergency_phone",
                ],
            },
            {
                "id": "passport",
                "title": _("Passport information"),
                "fields": [
                    "birth_name",
                    "passport_number",
                    "passport_expiration_date",
                ],
            },
        ]

    @property
    def form_widgets(self):
        # Hide fields
        res = super(MuskathlonTripForm, self).form_widgets
        res.update(
            {"passport_expiration_date": "cms.form.widget.date.ch", }
        )
        return res

    @property
    def form_title(self):
        return _("Personal information for the Muskathlon trip")

    @property
    def submit_text(self):
        return _("Save")

    @property
    def form_msg_success_updated(self):
        return _("Trip information updated.")

    def _form_validate_emergency_phone(self, value, **req_values):
        if value and not re.match(r"^[+\d][\d\s]{7,}$", value, re.UNICODE):
            return "emergency_phone", _("Please enter a valid phone number")
        # No error
        return 0, 0

    def _form_validate_passport_number(self, value, **req_values):
        return self._form_validate_alpha_field("passport_number", value)

    def _form_validate_emergency_name(self, value, **req_values):
        return self._form_validate_alpha_field("emergency_name", value)

    def _form_validate_birth_name(self, value, **req_values):
        return self._form_validate_alpha_field("birth_name", value)

    def _form_validate_passport_expiration_date(self, value, **req_values):
        valid = True
        old = False
        try:
            date = datetime.strptime(value, "%Y-%m-%d")
            today = datetime.now()
            old = date < today
            valid = not old
        except (ValueError, TypeError):
            valid = False
        finally:
            if not valid:
                message = _("Please enter a valid date")
                if old:
                    message = _("Your passport must be renewed!")
                return "passport_expiration_date", message
        # No error
        return 0, 0

    def _form_validate_alpha_field(self, field, value):
        if value and not re.match(r"^[\w\s'-]+$", value, re.UNICODE):
            return field, _("Please avoid any special characters")
        # No error
        return 0, 0

    def form_before_create_or_update(self, values, extra_values):
        """ Dismiss any pending status message, to avoid multiple
        messages when multiple forms are present on same page.
        """
        # Don't remove passport expiration date
        if not values.get("passport_expiration_date", True):
            del values["passport_expiration_date"]
        # Mark tasks as done
        if (
                values.get("passport_number")
                and values.get("passport_expiration_date")
                and values.get("emergency_name")
        ):
            values["completed_task_ids"] = [
                (4, self.env.ref("muskathlon.task_passport").id)
            ]
        self.o_request.website.get_status_message()

    def _form_write(self, values):
        """Write as Muskathlon to avoid any security restrictions."""
        uid = self.env.ref("muskathlon.user_muskathlon_portal").id
        # pass a copy to avoid pollution of initial values by odoo
        self.main_object.sudo(uid).write(values.copy())


class FlightDetailsForm(models.AbstractModel):
    _name = "cms.form.muskathlon.flight.details"
    _inherit = "cms.form"

    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_flight_details"
    _form_model = "event.flight"
    _form_model_fields = [
        "flight_number",
        "flying_company",
        "flight_type",
        "registration_id",
    ]
    _form_required_fields = [
        "flight_type",
        "registration_id",
        "flight_number",
        "departure_date",
        "departure_time",
        "arrival_date",
        "arrival_time",
        "flying_company",
    ]

    registration_id = fields.Integer()
    flight_type = fields.Char()
    departure_date = fields.Date()
    departure_time = fields.Char()
    arrival_date = fields.Date()
    arrival_time = fields.Char()

    @property
    def _form_fieldsets(self):
        return [
            {
                "id": "flight",
                "fields": [
                    "departure_date",
                    "departure_time",
                    "arrival_date",
                    "arrival_time",
                    "flight_type",
                    "flight_number",
                    "flying_company",
                ],
            },
        ]

    @property
    def form_title(self):
        return _("Flight details")

    @property
    def form_widgets(self):
        res = super(FlightDetailsForm, self).form_widgets
        res.update(
            {
                "flight_type": "cms_form_compassion.form.widget.hidden",
                "registration_id": "cms_form_compassion.form.widget.hidden",
                "departure_date": "cms.form.widget.date.ch",
                "departure_time": "cms.form.widget.time",
                "arrival_date": "cms.form.widget.date.ch",
                "arrival_time": "cms.form.widget.time",
            }
        )
        return res

    def _form_load_departure_date(self, fname, field, value, **req_values):
        return value or self._get_date(fname)[0]

    def _form_load_arrival_date(self, fname, field, value, **req_values):
        return value or self._get_date(fname)[0]

    def _form_load_departure_time(self, fname, field, value, **req_values):
        return value or self._get_date(fname)[1]

    def _form_load_arrival_time(self, fname, field, value, **req_values):
        return value or self._get_date(fname)[1]

    def _form_load_flight_type(self, fname, field, value, **req_values):
        return value or self.flight_type

    def _get_date(self, fname):
        if self.main_object:
            if "departure" in fname:
                date = self.main_object.departure
            else:
                date = self.main_object.arrival
        else:
            registration = self.env["event.registration"].browse(
                self.registration_id
            )
            if registration:
                if self.flight_type == "outbound":
                    date = registration.event_id.date_begin
                else:
                    date = registration.event_id.date_end
            else:
                date = None
        if date:
            local_tz = pytz.timezone(self.env.user.tz)
            full_date = date.replace(tzinfo=pytz.utc).astimezone(local_tz)
            return full_date.strftime("%d.%m.%Y"), full_date.strftime("%H:%M")
        else:
            # TODO : do we return none, an error or a date ?
            today = datetime.today().date()
            return today.strftime("%d.%m.%Y"), today.strftime("%H:%M")

    @property
    def submit_text(self):
        return _("Save")

    @property
    def form_msg_success_created(self):
        if self.flight_type == "outbound":
            return _(
                "Outbound flight entered. " "Please enter now the return flight."
            )
        return _("Return flight entered.")

    @property
    def form_msg_success_updated(self):
        return _("Flight details updated.")

    def form_init(self, request, main_object=None, **kw):
        form = super(FlightDetailsForm, self).form_init(request, main_object, **kw)
        # Store registration in form to get its values
        form.registration_id = kw.get("registration_id")
        form.flight_type = kw.get("flight_type")
        return form

    def form_before_create_or_update(self, values, extra_values):
        self.o_request.website.get_status_message()
        local_tz = pytz.timezone(self.env.user.tz)
        tz_offset = local_tz.utcoffset(datetime.now())
        if extra_values.get("departure_date"):
            departure = fields.Datetime.from_string(
                fields.Datetime.to_string(extra_values["departure_date"])
                + " " + extra_values["departure_time"] + ":00 "
            ) - tz_offset
            arrival = fields.Datetime.from_string(
                fields.Datetime.to_string(extra_values["arrival_date"])
                + " " + extra_values["arrival_time"] + ":00 "
            ) - tz_offset
            values.update(
                {
                    "registration_id": self.registration_id,
                    "flight_type": self.flight_type,
                    "departure": departure,
                    "arrival": arrival,
                }
            )

    def form_after_create_or_update(self, values, extra_values):
        """ Dismiss any pending status message, to avoid multiple
        messages when multiple forms are present on same page.
        """
        # Mark tasks as done
        registration = self.main_object.registration_id.sudo()
        if len(registration.flight_ids) == 2:
            registration.completed_task_ids += self.env.ref(
                "muskathlon.task_flight_details"
            )


class PassportForm(models.AbstractModel):
    _name = "cms.form.muskathlon.passport"
    _inherit = "cms.form"

    _form_model = "event.registration"
    _form_model_fields = ["passport"]
    _form_required_fields = ["passport"]
    form_id = "modal_passport"

    passport = fields.Binary()

    @property
    def form_msg_success_updated(self):
        return _("Passport successfully uploaded.")

    @property
    def form_widgets(self):
        # Hide fields
        res = super(PassportForm, self).form_widgets
        res["passport"] = "cms_form_compassion.form.widget.document"
        return res

    def _form_validate_passport(self, value, **req_values):
        if value == "":
            return "passport", _("Missing")
        return 0, 0

    def form_before_create_or_update(self, values, extra_values):
        if values.get("passport"):
            # Mark the task criminal record as completed
            passport_task = self.env.ref("muskathlon.task_scan_passport")
            values["completed_task_ids"] = [(4, passport_task.id)]
        else:
            del values["completed_task_ids"]
