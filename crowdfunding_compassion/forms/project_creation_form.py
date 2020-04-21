##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, _

_logger = logging.getLogger(__name__)


class ProjectCreationForm(models.AbstractModel):
    _name = "cms.form.crowdfunding.project"
    _inherit = ["cms.form"]

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
    _form_required_fields = ("name", "type", "deadline")

    # _display_type = "full"

    @property
    def form_title(self):
        return _("Create your project")

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
        }, {
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
        # override to remove text saying item updated after registration
        return

    # Form submission
    #################
    # TODO change the way we get the partner_id, as it is a public route
    def form_before_create_or_update(self, values, extra_values):
        owner = self.env["crowdfunding.participant"].sudo().search([
            ("partner_id", "=", self.env.user.partner_id.id)
        ])
        if not owner:
            owner = self.env["crowdfunding.participant"].sudo().create({
                "partner_id": self.env.user.partner_id.id
            })
        values.update({
            "project_owner_id": owner.id
        })
        super().form_before_create_or_update(values, extra_values)

    def _form_write(self, values):
        """ Nothing to do on write, we handle everything in other methods.
        """
        return True

    def form_after_create_or_update(self, values, extra_values):
        comm_obj = self.env["partner.communication.job"]
        config = self.env.ref("crowdfunding_compassion.config_project_confirmation")
        comm_obj.create(
            {
                "config_id": config.id,
                "partner_id": self.env.user.partner_id.id,
                "object_ids": self.main_object.id,
            }
        )

    def form_next_url(self, main_object=None):
        return super().form_next_url(self.main_object)
