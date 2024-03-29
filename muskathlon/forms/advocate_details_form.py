##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, _


class AdvocateDetailsForm(models.AbstractModel):
    _name = "cms.form.advocate.details"
    _inherit = "cms.form"

    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_advocate_details"
    _form_model = "advocate.details"
    _form_model_fields = ["quote", "mail_copy_when_donation"]
    _form_fields_order = [
        "quote",
        "mail_copy_when_donation",
    ]
    _form_required_fields = ["quote"]

    quote = fields.Text(
        string="My motto",
        default="",
        help="Write a small quote that will appear on your profile page "
             "and will be used in thank you letters your donors will "
             "receive.",
    )
    mail_copy_when_donation = fields.Boolean(
        string="E-mail notification when you receive a donation"
    )

    @property
    def form_title(self):
        return _("About me")

    @property
    def submit_text(self):
        return _("Save")

    @property
    def form_msg_success_updated(self):
        return _("Profile updated.")

    def form_before_create_or_update(self, values, extra_values):
        """ Dismiss any pending status message, to avoid multiple
        messages when multiple forms are present on same page.
        """
        self.o_request.website.get_status_message()
