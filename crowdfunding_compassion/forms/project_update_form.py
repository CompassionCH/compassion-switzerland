##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import re

from odoo import models, _


class PartnerCoordinatesForm(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.update"
    _inherit = "cms.form"

    form_buttons_template = "cms_form_compassion.modal_form_buttons"
    form_id = "modal_crowdfunding_project_update"
    _form_model = "crowdfunding.project"
    _form_model_fields = [
        "name",
        "description",
        "personal_motivation",
        "deadline",
        "cover_photo",
        "presentation_video",
        "facebook_url",
        "twitter_url",
        "instagram_url",
        "personal_web_page_url",
        "type",
    ]

    @property
    def _form_fieldsets(self):
        fieldset = [{
            "id": "project",
            "title": _("Your project"),
            "fields": [
                "name",
                "description",
                "personal_motivation",
                "deadline",
                "cover_photo",
                "type",
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
            "deadline": "cms.form.widget.date.ch",
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
        self.o_request.website.get_status_message()
