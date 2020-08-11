##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from datetime import datetime

import logging
from base64 import b64encode, b64decode
from PIL import Image
from io import BytesIO

import re

from odoo import models, fields, _
from odoo.tools import file_open

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
            2: {"form_model": "cms.form.crowdfunding.project.step2"},
            3: {"form_model": "cms.form.crowdfunding.project.step3"},
        }

    @property
    def form_msg_success_created(self):
        # override to remove text saying item updated after registration
        return

    def form_after_create_or_update(self, values, extra_values):
        super().form_after_create_or_update(values, extra_values)
        # Dismiss default status message
        self.o_request.website.get_status_message()

    def form_process(self):
        super().form_process()

        storage = self.wiz_storage_get()
        curr_step = storage.get("current")
        if curr_step:
            step_data = storage.get("steps")[curr_step]
            if step_data.get("name"):
                step_data["campaign_name"] = step_data["name"]
            self.form_render_values['form_data'] = step_data

    def form_next_url(self, main_object=None):
        direction = self.request.form.get("wiz_submit")
        if direction == "prev":
            step_values = self._prepare_step_values_to_store(self.request.form, {})
            self.wiz_save_step(step_values)
        return super().form_next_url(main_object) + "?save=True"

    @staticmethod
    def compress_big_images(b64_data):
        """
        Method that tries to compress an image receveived as parameter if this
        image is too big (greater than 200KB). If the image is small enough or
        if the compression does not improve the results, we simply return the
        old version of the image.

        :param b64_data: the data of the image to compress, expressed as a
        base64 string.
        :return: either the original image, if it is small enough (<200KB)
        or if the compression does not reduce size, or a new image that has
        been compressed, again as a base64 string.
        """
        def resize(image):
            width, height = image.size
            min_width, min_height = min(width, 900), min(height, 400)
            factor = max(min_width / width, min_height / height)
            return image.resize((int(width * factor), int(height * factor)))

        def compress(image):
            buffer = BytesIO()
            image.convert("RGB").save(buffer, format='JPEG', optimize=True)
            return b64encode(buffer.getvalue())

        old_image = b64_data
        # If length in byte is greater than 200KB
        max_bytes_size, bytes_len = 2e5, 3 * (len(b64_data) / 4)
        if bytes_len > max_bytes_size:
            bytes_data = BytesIO(b64decode(b64_data))
            img = Image.open(bytes_data)
            new_image = compress(resize(img))
            new_bytes_len = 3 * (len(new_image) * 4)
            # We don't change the image if there is no improvement
            return new_image if bytes_len > new_bytes_len else old_image
        return old_image

    def sanitized_url(values, key):
        def validate_url(url):
            """ Reference: https://github.com/django/django/blob/master/django/core/validators.py """
            url_regex = re.compile(
                r'^https?://'  # http:// or https://
                r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
                r'localhost|'  # localhost...
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}|'  # ...or ipv4
                r'\[?[A-F0-9]*:[A-F0-9:]+\]?)'  # ...or ipv6
                r'(?::\d+)?'  # optional port
                r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            return url_regex.match(url)

        # Prevent the URL to be considered as a route if necessary
        if values.get(key):
            url = values[key]
            if not url.startswith("http"):
                url = "https://" + url
            if not validate_url(url):
                raise InvalidLinkException
            return url
        return None


class ProjectCreationFormStep1(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.step1"
    _inherit = "cms.form.crowdfunding.wizard"

    campaign_name = fields.Char(
        "Name of your project",
        help="Use a catchy name that is accurate to your idea.",
        required=True
    )

    _form_model_fields = [
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
                "campaign_name",
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
        if kw.get("refresh") and self._wiz_storage_key in self._wiz_storage:
            del self._wiz_storage[self._wiz_storage_key]
        super().wiz_init(page, **kw)

    def form_get_widget(self, fname, field, **kw):
        """Retrieve and initialize widget."""
        if fname == "deadline":
            if kw is None:
                kw = {}
            kw["min_date"] = datetime.now().isoformat()
        return self.env[self.form_get_widget_model(fname, field)].widget_init(
            self, fname, field, **kw
        )

    def form_after_create_or_update(self, values, extra_values):
        if values["deadline"] < datetime.now().date():
            raise InvalidDateException
        if values.get("cover_photo"):
            values["cover_photo"] = ProjectCreationWizard\
                .compress_big_images(values["cover_photo"])
        for key in ["presentation_video",
                    "facebook_url",
                    "twitter_url",
                    "instagram_url",
                    "personal_web_page_url"]:
            values[key] = ProjectCreationWizard.sanitized_url(values, key)
        super().form_after_create_or_update(values, extra_values)

    @property
    def form_widgets(self):
        res = super().form_widgets
        res.update({
            "deadline": "cms.form.widget.date.ch",
            "cover_photo": "cms_form_compassion.form.widget.simple.image"
        })
        return res

    def form_before_create_or_update(self, values, extra_values):
        super().form_before_create_or_update(values, extra_values)
        # Put name of campaign in correct field
        values["name"] = extra_values.pop("campaign_name")

    def _form_create(self, values):
        """ Holds the creation for the last step. The values will be passed
        to the next steps. """
        pass


class InvalidLinkException(Exception):
    def __init__(self):
        super().__init__("Invalid link")


class InvalidDateException(Exception):
    def __init__(self):
        super().__init__("Invalid date")


class NoGoalException(Exception):
    def __init__(self):
        super().__init__("No goal")


class NegativeGoalException(Exception):
    def __init__(self):
        super().__init__("Negative goal")


class ProjectCreationStep2(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.step2"
    _inherit = "cms.form.crowdfunding.wizard"

    _form_model_fields = ['product_id']
    _form_fields_hidden = [
        'product_id', 'participant_product_number_goal',
        'participant_number_sponsorships_goal'
    ]

    participant_product_number_goal = fields.Integer()
    participant_number_sponsorships_goal = fields.Integer()

    def form_before_create_or_update(self, values, extra_values):
        product_goal = extra_values.get('participant_product_number_goal')
        sponsorship_goal = extra_values.get('participant_number_sponsorships_goal')

        # Existing projects with sponsorship and fund chosen must have both
        if self.main_object:
            if self.main_object.product_id and \
                    self.main_object.number_sponsorships_goal:
                if not product_goal or not sponsorship_goal:
                    raise NoGoalException
        else:
            # New projects must have at least either a sponsorship or a fund objective
            if not product_goal and not sponsorship_goal:
                raise NoGoalException
            elif product_goal and int(product_goal) < 0 or sponsorship_goal and int(
                    sponsorship_goal) < 0:
                raise NegativeGoalException

        if not product_goal:
            values["product_id"] = False
        super().form_before_create_or_update(values, extra_values)

    def _form_create(self, values):
        """ Holds the creation for the last step. The values will be passed
        to the next steps. """
        pass

    def _form_write(self, values):
        pass

    def form_next_url(self, main_object=None):
        url = super().form_next_url(main_object)
        if main_object:
            url += f"&project_id={main_object.id}"
        return url


class ProjectCreationStep3(models.AbstractModel):
    _name = "cms.form.crowdfunding.project.step3"
    _inherit = ["cms.form.crowdfunding.wizard", "cms.form.match.partner"]

    _form_model_fields = ['product_id']

    partner_image = fields.Binary(
        "Profile picture",
        help="Upload a profile picture, square 800 x 800px")
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
                "partner_title",
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
        if storage.get(1, {}).get("type") == "collective" or self.main_object:
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

    def form_get_widget(self, fname, field, **kw):
        """Retrieve and initialize widget."""
        if fname == "partner_birthdate":
            if kw is None:
                kw = {}
            kw["max_date"] = datetime.now().isoformat()
        return self.env[self.form_get_widget_model(fname, field)].widget_init(
            self, fname, field, **kw
        )

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
        # Put a default spoken language
        if "partner_birthdate" in extra_values and \
                extra_values["partner_birthdate"] > datetime.now().date():
            raise InvalidDateException
        for key in ["participant_facebook_url",
                    "participant_twitter_url",
                    "participant_instagram_url",
                    "participant_personal_web_page_url"]:
            extra_values[key] = ProjectCreationWizard\
                .sanitized_url(extra_values, key)
        language = self.env["res.lang.compassion"].search([
            ("lang_id.code", "=", self.env.lang)], limit=1)
        values["partner_spoken_lang_ids"] = [(4, language.id)]
        super().form_before_create_or_update(values, extra_values)
        # Take values from previous steps
        storage = self.wiz_storage_get().get('steps')
        values.update(storage.get(1, {}))
        values.update(storage.get(2, {}))

    def _form_create(self, values):
        """Called for new project.
         Create as root and avoid putting Admin as follower. """
        values["project_owner_id"] = values.pop("partner_id")
        self.main_object = self.form_model.sudo().with_context(
            tracking_disable=True).create(values.copy())

    def _form_write(self, values):
        """This is called when project already exists and participant is joining."""
        self.participant_id = self.env["crowdfunding.participant"].sudo().create({
            "partner_id": values["partner_id"],
            "project_id": self.main_object.sudo().id,
        })

    def form_after_create_or_update(self, values, extra_values):
        super().form_after_create_or_update(values, extra_values)
        if self.participant_id:
            config = self.env.ref(
                "crowdfunding_compassion.config_project_join").sudo()
            participant = self.participant_id.sudo()
            partner = participant.partner_id.sudo()

        else:
            config = self.env.ref(
                "crowdfunding_compassion.config_project_confirmation").sudo()
            participant = self.main_object.sudo().participant_ids
            partner = self.main_object.sudo().project_owner_id.sudo()

        if extra_values.get('partner_image'):
            extra_values["partner_image"] = ProjectCreationWizard\
                .compress_big_images(extra_values["partner_image"])
            partner.write({"image": extra_values["partner_image"]})
        else:
            path = "crowdfunding_compassion/static/src/img/guy.png"
            if partner.title.gender == "F":
                path = "crowdfunding_compassion/static/src/img/lady.png"
            partner.write({
                "image": b64encode(file_open(path, "rb").read())})

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

        # Notify staff of new participant
        settings = self.env["res.config.settings"].sudo()
        notify_ids = settings.get_param("new_participant_notify_ids")
        if notify_ids:
            participant.partner_id.message_post(
                subject=_("New Crowdfunding participant"),
                body=_(
                    "%s created or joined a project. "
                    "A user may need to be created if he doesn't have access"
                )
                % participant.partner_id.name,
                partner_ids=notify_ids,
                type="comment",
                subtype="mail.mt_comment",
                content_subtype="plaintext",
            )

    def form_next_url(self, main_object):
        direction = self.request.form.get('wiz_submit', 'next')
        if direction == 'next':
            return f"/projects/create/confirm/{main_object.id}"
        else:
            return super().form_next_url(main_object)
