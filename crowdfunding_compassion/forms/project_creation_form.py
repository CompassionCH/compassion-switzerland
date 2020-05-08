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
    _form_extra_css_klass = "crowdfunding_project_creation_from"
    _wiz_name = _name

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

    def form_after_create_or_update(self, values, extra_values):
        super().form_after_create_or_update(values, extra_values)
        # Dismiss default status message
        self.o_request.website.get_status_message()


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
            "id": "type",
            "title": _("My project is"),
            "description": _(
                "Choose if you are doing your project alone, or if you want to open "
                "it to other fundraisers (ie: collective sport projects)"),
            "fields": ["type"]
        }, {
            "id": "social_medias",
            "title": _("Social Medias"),
            "description": _(
                "If you have any social media account that you use to promote your "
                "project, you can link them to your personal page."),
            "fields": [
                "facebook_url",
                "twitter_url",
                "instagram_url",
                "personal_web_page_url",
            ],
        }]
        return fieldset

    def wiz_init(self, page=1, **kw):
        # Flush storage to avoid using old values from previous session
        if self._wiz_storage_key in self._wiz_storage:
            del self._wiz_storage[self._wiz_storage_key]
        super().wiz_init(page, **kw)

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


class NoGoalException(Exception):
    def __init__(self):
        super().__init__("No goal")


class ProjectCreationStep2(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.step2"
    _inherit = "cms.form.crowdfunding.wizard"

    _form_model_fields = ['product_id']
    _form_fields_hidden = [
        'product_id', 'participant_product_number_goal',
        'participant_number_sponsorships_goal', 'no_product'
    ]

    no_product = fields.Boolean()
    participant_product_number_goal = fields.Integer()
    participant_number_sponsorships_goal = fields.Integer()

    def form_before_create_or_update(self, values, extra_values):
        product_goal = extra_values.get('participant_product_number_goal')
        sponsorship_goal = extra_values.get('participant_number_sponsorships_goal')
        if not product_goal and not sponsorship_goal:
            raise NoGoalException

    def _form_create(self, values):
        """ Holds the creation for the last step. The values will be passed
        to the next steps. """
        pass

    def _form_write(self, values):
        pass

    def form_next_url(self, main_object=None):
        url = super().form_next_url(main_object)
        if main_object:
            url += f"?project_id={main_object.id}"
        return url


class ProjectCreationStep3(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.step3"
    _inherit = ["cms.form.crowdfunding.wizard", "cms.form.match.partner"]

    _form_model_fields = ['product_id']

    partner_image = fields.Binary(
        "Profile picture",
        help="Upload a profile picture, square 800 x 800px",
        required=True)
    participant_personal_motivation = fields.Text(
        "Personal motivation",
        help="Tell the others what is inspiring you, why it matters to you.",
        required=True
    )
    participant_facebook_url = fields.Char("Facebook link")
    participant_twitter_url = fields.Char("Twitter link")
    participant_instagram_url = fields.Char("Instagram link")
    participant_personal_web_page_url = fields.Char("Personal web page")
    participant_id = fields.Many2one("crowdfunding.participant")

    @property
    def _form_fieldsets(self):
        fieldset = [{
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
                "partner_image"
            ],
        }]
        storage = self.wiz_storage_get().get('steps')
        if self.main_object or storage.get(2, {}).get("type") == "collective":
            # Add personal motivation at first
            fieldset[0]["fields"].insert(0, "participant_personal_motivation")
            # Add social media info for the participant
            fieldset.append({
                "id": "social_medias",
                "title": _("Social Medias"),
                "description": _(
                    "If you have any social media account that you use to promote your "
                    "project, you can link them to your personal page."),
                "fields": [
                    "participant_facebook_url",
                    "participant_twitter_url",
                    "participant_instagram_url",
                    "participant_personal_web_page_url",
                ],
            })
        return fieldset

    @property
    def form_widgets(self):
        res = super().form_widgets
        res.update({
            "partner_image": "cms_form_compassion.form.widget.simple.image",
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
        # Take values from previous steps
        storage = self.wiz_storage_get().get('steps')
        values.update(storage.get(1, {}))
        values.update(storage.get(2, {}))

    def _form_create(self, values):
        """Called for new project.
         Create as root and avoid putting Admin as follower. """
        if values.get("no_product") == "on":
            values["product_id"] = False
        values["project_owner_id"] = values.pop("partner_id")
        self.main_object = self.form_model.sudo().with_context(
            tracking_disable=True).create(values.copy())

    def _form_write(self, values):
        """This is called when project already exists and participant is joining."""
        self.participant_id = self.env["crowdfunding.participant"].sudo().create({
            "partner_id": values["partner_id"],
            "project_id": self.main_object.sudo().id
        })

    def form_after_create_or_update(self, values, extra_values):
        super().form_after_create_or_update(values, extra_values)
        if self.participant_id:
            config = self.env.ref(
                "crowdfunding_compassion.config_project_join").sudo()
            participant = self.participant_id
            partner = self.participant_id.partner_id

        else:
            config = self.env.ref(
                "crowdfunding_compassion.config_project_confirmation").sudo()
            participant = self.main_object.sudo().participant_ids
            partner = self.main_object.sudo().project_owner_id
        extra_values.update(values)
        participant_values = {
            key.replace("participant_", ""): val for key, val in extra_values.items()
            if key.startswith("participant_") and val
        }
        participant.sudo().write(participant_values)
        comm_obj = self.env["partner.communication.job"].sudo()
        comm_obj.create({
            "config_id": config.id,
            "partner_id": partner.id,
            "object_ids": self.main_object.sudo().id,
        })

    def form_next_url(self, main_object):
        return f"/projects/create/confirm/{main_object.id}"
