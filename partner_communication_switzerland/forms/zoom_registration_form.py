from psycopg2 import IntegrityError

from odoo import models, fields, _
from odoo.exceptions import ValidationError, UserError


class ZoomRegistrationForm(models.AbstractModel):
    _name = "cms.form.res.partner.zoom.attendee"
    _inherit = "cms.form.match.partner"

    _form_model = "res.partner.zoom.attendee"

    form_buttons_template = 'cms_form_compassion.simple_form_buttons'
    inform_me_for_next_zoom = fields.Boolean(
        "I am not available", help="Please inform me for the next Zoom session"
    )

    def _form_load_zoom_session_id(self, fname, field, value, **req_values):
        return value or req_values.get(fname, self.main_object.zoom_session_id.id)

    @property
    def _form_fieldsets(self):
        return [
            {
                "id": "partner",
                "fields": [
                    "partner_firstname",
                    "partner_lastname",
                    "partner_email",
                    "partner_phone",
                ]
            },
            {
                "id": "other_info",
                "fields": [
                    "inform_me_for_next_zoom",
                    "optional_message",
                    "zoom_session_id"
                ]
            }
        ]

    @property
    def form_widgets(self):
        # Hide fields
        res = super(ZoomRegistrationForm, self).form_widgets
        res["zoom_session_id"] = "cms_form_compassion.form.widget.hidden"
        return res

    def form_make_field_wrapper_klass(self, fname, field, **kw):
        """ Center the form in the page. """
        res = super().form_make_field_wrapper_klass(fname, field, **kw)
        res += " row justify-content-center px-4"
        return res

    def form_before_create_or_update(self, values, extra_values):
        super().form_before_create_or_update(values, extra_values)
        if extra_values.get("inform_me_for_next_zoom"):
            values["state"] = "declined"
        else:
            values["state"] = "confirmed"

    def _form_create(self, values):
        # Create as sudo user
        attendee_obj = self.form_model.sudo()
        try:
            attendee = attendee_obj.search([
                ("partner_id", "=", values["partner_id"]),
                ("zoom_session_id", "=", int(values["zoom_session_id"])),
                ("state", "=", "invited")
            ])
            if attendee:
                attendee.write(values.copy())
            else:
                attendee = attendee_obj.create(values.copy())
            self.main_object = attendee
        except IntegrityError:
            # Make error message more friendly
            raise IntegrityError(_("You are already registered for this session."))

    def form_after_create_or_update(self, values, extra_values):
        if extra_values.get("inform_me_for_next_zoom"):
            self.main_object.sudo().inform_about_next_session()
        if values.get("optional_message"):
            self.main_object.sudo().notify_user()
        self.main_object.sudo().send_confirmation()

    @property
    def form_msg_success_created(self):
        return _("Thank you for your registration,"
                 "you will get a confirmation by email.")
