##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, fields, _

_logger = logging.getLogger(__name__)


class ProjectCreationWizard(models.AbstractModel):
    _name = "cms.form.crowdfunding.wizard"
    _inherit = "cms.form.wizard"
    _form_model = "crowdfunding.project"

    def _wiz_base_url(self):
        return "/projects/create"

    def form_check_permission(self, raise_exception=True):
        # no need for this
        pass

    def wiz_configure_steps(self):
        return {
            1: {"form_model": "cms.form.crowdfunding.project.step1"},
            2: {"form_model": "cms.form.crowdfunding.project.step1"},
            3: {"form_model": "cms.form.crowdfunding.project.step1"},
        }

    @property
    def form_msg_success_created(self):
        # override to remove text saying item updated after registration
        return


class ProjectCreationFormStep1(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.step1"
    _inherit = "cms.form.crowdfunding.wizard"

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
    def form_title(self):
        return _("Create your project")

    @property
    def _form_fieldsets(self):
        fieldset = [{
            "id": "project",
            "fields": [
                "name",
                "description",
                "personal_motivation",
                "deadline",
                "cover_photo",
                "presentation_video",
            ],
        }, {
            "id": "social_medias",
            "title": _("Social Medias"),
            "description": _("If you have any social media account that you use to "
                             "promote your project, you can link them to your "
                             "personal page."),
            "fields": [
                "facebook_url",
                "twitter_url",
                "instagram_url",
                "personal_web_page_url",
            ],
        }, {
            "id": "type",
            "title": _("My project is"),
            "description": _(
                "Choose if you are doing your project alone, or if you want to open "
                "it to other fundraisers (ie: collective sport projects)"),
            "fields": ["type"]
        }]
        return fieldset

    @property
    def form_widgets(self):
        res = super().form_widgets
        res.update({
            "deadline": "cms.form.widget.date.ch",
            "cover_photo": "cms_form_compassion.form.widget.simple.image"
        })
        return res

    def _form_create(self, values):
        """ Holds the creation for the last step. The values will be passed
        to the next steps. """
        pass


class ProjectCreationStep2(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.step2"
    _inherit = "cms.form.crowdfunding.wizard"

    _form_model_fields = [
        'product_id', 'product_number_goal', 'number_sponsorships_goal'
    ]
    _form_fields_hidden = [
        'product_id', 'product_number_goal', 'number_sponsorships_goal'
    ]

    def _form_create(self, values):
        """ Holds the creation for the last step. The values will be passed
        to the next steps. """
        pass


class ProjectCreationStep3(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.step3"
    _inherit = ["cms.form.crowdfunding.wizard", "cms.form.match.partner"]

    _form_model_fields = [
        'product_id', 'product_number_goal', 'number_sponsorships_goal'
    ]

    profile_picture = fields.Binary(
        help="Upload a profile picture, square 800 x 800px",
        required=True)

    @property
    def _form_fieldsets(self):
        return [{
            "id": "project",
            "fields": [
                "partner_firstname",
                "partner_lastname",
                "partner_birthdate",
                "partner_street",
                "partner_zip",
                "partner_city",
                "partner_country_id",
                "partner_email",
                "partner_phone",
                "profile_photo"
            ],
        }]

    @property
    def form_widgets(self):
        res = super().form_widgets
        res.update({
            "profile_photo": "cms_form_compassion.form.widget.simple.image",
            "partner_birthdate": "cms.form.widget.date.ch",
        })
        return res

    def _form_load_partner_id(self, fname, field, value, **req_values):
        # Try fetching the partner if he is already connected.
        return value or req_values.get(fname, self.env.user.partner_id.sudo().id)

    def _load_partner_field(self, fname, **req_values):
        # Try fetching the partner if he is already connected.
        partner = self.env.user.partner_id.sudo()
        pf_name = fname.split("partner_")[1]
        return req_values.get(fname, getattr(partner.sudo(), pf_name, ""))

    # Form submission
    #################
    def form_before_create_or_update(self, values, extra_values):
        super().form_before_create_or_update(values, extra_values)
        values["project_owner_id"] = values.pop("partner_id")
        # Take values from previous steps
        storage = self.wiz_storage_get().get('steps')
        values.update(storage.get(1, {}))
        values.update(storage.get(2, {}))

    def _form_create(self, values):
        """ Create as root and avoid putting Admin as follower. """
        self.main_object = self.form_model.sudo().with_context(
            tracking_disable=True).create(values.copy())

    def form_after_create_or_update(self, values, extra_values):
        comm_obj = self.env["partner.communication.job"].sudo()
        config = self.env.ref(
            "crowdfunding_compassion.config_project_confirmation").sudo()
        comm_obj.create(
            {
                "config_id": config.id,
                "partner_id": self.main_object.project_owner_id.id,
                "object_ids": self.main_object.id,
            }
        )

    def form_next_url(self, main_object=None):
        return "/projects/create/confirm"
