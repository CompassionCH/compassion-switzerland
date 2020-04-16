##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from datetime import datetime, timedelta

from odoo import models, fields, tools, _

testing = tools.config.get("test_enable")
_logger = logging.getLogger(__name__)


if not testing:

    class ProjectCreationForm(models.AbstractModel):
        _name = "cms.form.crowdfunding.project"
        _inherit = ["cms.form"]

        _form_model = "crowdfunding.project"
        _form_model_fields = [
            "description",
            "personal_motivation",
            "cover_photo",
            "presentation_video",
            "facebook_url",
            "twitter_url",
            "instagram_url",
            "personal_web_page_url",
        ]
        _form_required_fields = ("name", "type", "deadline", "project_owner_id", "state")
        _display_type = "full"

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
                    "presentation_video",
                ],
            }, {
                "id": "social_medias",
                "title": _("Social Medias"),
                "fields": [
                    "facebook_url",
                    "twitter_url",
                    "instagram_url"
                    "personal_web_page_url"
                ],
            }]
            return fieldset

        @property
        def form_widgets(self):
            # Hide fields
            res = super().form_widgets
            res.update({
                "deadline": "cms.form.widget.date.ch",
            })
            return res

        @property
        def form_msg_success_updated(self):
            # override to remove text saying item updated after registration
            return

        # Form submission
        #################
        def form_before_create_or_update(self, values, extra_values):
            project = self.main_object.sudo()
            # values["partner_id"] = sponsorship.partner_id.id
            super().form_before_create_or_update(values, extra_values)

        def _form_write(self, values):
            """ Nothing to do on write, we handle everything in other methods.
            """
            return True

        # def form_after_create_or_update(self, values, extra_values):
        #     delay = datetime.now() + timedelta(seconds=3)
        #     sponsorship = self.main_object.sudo()
        #     pay_first_month_ebanking = extra_values.get("pay_first_month_ebanking")
        #     sponsorship.with_delay(eta=delay).finalize_form(
        #         pay_first_month_ebanking, values["payment_mode_id"]
        #     )
        #     if pay_first_month_ebanking and sponsorship.sms_request_id.new_partner:
        #         delay = datetime.now() + timedelta(seconds=5)
        #         sponsorship.with_delay(eta=delay).create_first_sms_invoice()
        #     message_post_values = self._get_post_message_values(extra_values)
        #     if message_post_values:
        #         body = "<ul>{}</ul>".format(
        #             "".join(
        #                 [
        #                     "<li>{}: {}</li>".format(k, v)
        #                     for k, v in message_post_values.items()
        #                 ]
        #             )
        #         )
        #         sponsorship.with_delay().post_message_from_step2(body)
        #     # Store payment setting for redirection
        #     self.pay_first_month_ebanking = pay_first_month_ebanking

        def form_next_url(self, main_object=None):
            return super().form_next_url(main_object)
