##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import models, api, _

_logger = logging.getLogger(__name__)


class MailTrackingEvent(models.Model):
    _inherit = "mail.tracking.event"

    def send_mails_to_partner_and_staff(
            self, tracking_email, metadata, staff_email_body
    ):
        partner = tracking_email.partner_id
        if partner:
            self._invalid_email(tracking_email)
            to_write = {"invalid_mail": partner.email, "email": False}

            staff_ids = (
                self.env["res.config.settings"]
                    .sudo()
                    .get_param("invalid_mail_notify_ids")
            )
            del to_write["email"]
            subject = _(
                "Email invalid! An error occurred: " + metadata.get("error_type", "")
            )
            body = _(staff_email_body)
            partner.message_post(
                body=body,
                subject=subject,
                partner_ids=staff_ids,
                type="comment",
                subtype="mail.mt_comment",
                content_subtype="plaintext",
            )
            partner.write(to_write)

    @api.model
    def process_hard_bounce(self, tracking_email, metadata):
        body = (
            "Warning : Sponsor's Email is invalid!\nError description: "
            + metadata.get("error_description", "")
        )
        self.send_mails_to_partner_and_staff(tracking_email, metadata, body)
        return super().process_hard_bounce(tracking_email, metadata)

    @api.model
    def process_soft_bounce(self, tracking_email, metadata):
        body = _(
            "Warning : Sponsor's Email is invalid!\n Error description: "
            + metadata.get("error_description", "")
        )
        self.send_mails_to_partner_and_staff(tracking_email, metadata, body)
        return super().process_soft_bounce(tracking_email, metadata)

    @api.model
    def process_unsub(self, tracking_email, metadata):
        """
        Opt out partners when they unsubscribe.
        """
        tracking_email.partner_id.opt_out = True
        tracking_email.partner_id.message_post(
            body=_("Partner Unsubscribed from marketing e-mails"),
            subject=_("Opt-out")
        )
        return super().process_unsub(tracking_email, metadata)

    @api.model
    def process_reject(self, tracking_email, metadata):
        body = _(
            "Warning : There is a problem with this Sponsor's Email. \n"
            "reason: " + metadata.get("error_type", "")
        )
        self.send_mails_to_partner_and_staff(tracking_email, metadata, body)

        return super().process_reject(tracking_email, metadata)

    def _invalid_email(self, tracking_email):
        """
        Sends invalid e-mail communication.
        In particular cases avoid sending the communciation because it will append later on
        in an other process :
        - if the invalid event came from an email linked to a correspondence (b2s)
        - if the invalid event came from an email link to the onboarding confirmation
        """
        
        # invalid config to send to the partner
        invalid_comm = self.env.ref("partner_communication_switzerland.wrong_email")

        # correspondence mail should return b2s email not read
        correspondence_email = tracking_email.filtered(
            lambda x: x.mail_id.model == "partner.communication.job" and
                      self.env["partner.communication.job"].browse(
                          x.mail_id.res_id).model == "correspondence"
        )

        # other special case for onboarding welcome not read
        onboarding_welcome_config = self.env.ref(
            "partner_communication_switzerland.config_onboarding_sponsorship_confirmation")

        onboarding_welcome_email = tracking_email.filtered(
            lambda x: x.mail_id.model == "partner.communication.job" and
                      self.env["partner.communication.job"].browse(
                          x.mail_id.res_id).config_id == onboarding_welcome_config
        )

        # even if the specific communication is not yet going out to the partner with
        # create a not on his/her odoo profile page
        tracking_email.partner_id.message_post(
            body=_("The email couldn't be sent due to invalid address"),
            subject=tracking_email.name
        )

        # in those case specific communication will be sent in another process
        # return to avoid duplication
        if correspondence_email or onboarding_welcome_email:
            return

        partner_id = tracking_email.partner_id.id
        if partner_id:
            self.env["partner.communication.job"].create(
                {
                    "config_id": invalid_comm.id,
                    "partner_id": partner_id,
                    "object_ids": partner_id,
                }
            )

    @api.model
    def process_spam(self, tracking_email, metadata):
        tracking_email.partner_id.message_post(
            body=_("The email was marked as spam by the partner"),
            subject=tracking_email.name
        )
