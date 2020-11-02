##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields, _


class PartnerCoordinatesForm(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.update"
    _inherit = "cms.form"

    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_crowdfunding_project_update"
    _form_model = "crowdfunding.project"
    _form_model_fields = [
        "description",
        "cover_photo",
        "presentation_video",
        "facebook_url",
        "twitter_url",
        "instagram_url",
        "personal_web_page_url",
    ]

    name = fields.Char()

    @property
    def _form_fieldsets(self):
        fieldset = [{
            "id": "project",
            "title": _("Your project"),
            "fields": [
                "name",
                "description",
                "cover_photo",
            ],
        },
            {
                "id": "social_medias",
                "title": _("Social Medias"),
                "fields": [
                    "presentation_video",
                    "facebook_url",
                    "twitter_url",
                    "instagram_url",
                    "personal_web_page_url",
                ],
            }]
        return fieldset

    @property
    def form_title(self):
        return _("Your project")

    @property
    def submit_text(self):
        return _("Save")

    @property
    def form_widgets(self):
        # Hide fields
        res = super().form_widgets
        res.update({
            "cover_photo": "cms_form_compassion.form.widget.simple.image"
        })
        return res

    @property
    def form_msg_success_updated(self):
        return _("Project updated.")

    def form_before_create_or_update(self, values, extra_values):
        """ Dismiss any pending status message, to avoid multiple
        messages when multiple forms are present on same page.
        """
        name = extra_values.get("name")
        if name:
            values["name"] = name
        self.o_request.website.get_status_message()

    def form_after_create_or_update(self, values, extra_values):
        if values.get("name") or values.get("description"):
            # Notify responsible of the changes, for validation.
            settings = self.env["res.config.settings"].sudo()
            notify_ids = settings.get_param("new_participant_notify_ids")
            if notify_ids:
                user = self.env["res.partner"].sudo().browse(notify_ids[0][2]) \
                    .mapped("user_ids")[:1]
                self.main_object.sudo().activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary="Verify project information.",
                    note=f"{self.main_object.project_owner_id.name} updated the "
                    f"name and description of the project. "
                    f"Please check if the information is good enough.",
                    user_id=user.id
                )
