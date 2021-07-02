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

    @api.model
    def process_delivered(self, tracking_email, metadata):
        """ Mark correspondence as read. """
        correspondence = self.env["correspondence"].search(
            [
                ("email_id", "=", tracking_email.mail_id.id),
                ("letter_delivered", "=", False),
            ]
        )
        correspondence.write({"letter_delivered": True})
        return super().process_delivered(tracking_email, metadata)

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
        - if the invalid event came from an email linked to a correspondence send child letter unread
        - if the invalid event came from an email link to the onboarding confirmation send unread confirmation
        """
        
        # invalid config to send to the partner
        invalid_comm = self.env.ref("partner_communication_switzerland.wrong_email")
        b2s_email_not_read = self.env.ref("partner_communication_switzerland.child_letter_unread")
        onboarding_welcome_email_not_read = self.env.ref(
            "partner_communication_switzerland.config_onboarding_sponsorship_confirmation_not_read")

        _config_id = invalid_comm
        _object_ids = None

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

        if correspondence_email:
            _config_id = b2s_email_not_read
            comm = self.env["partner.communication.job"].browse(
                correspondence_email.mail_id.res_id)
            _object_ids = comm.object_ids

        elif onboarding_welcome_email:
            _config_id = onboarding_welcome_email_not_read
            comm = self.env["partner.communication.job"].browse(
                onboarding_welcome_email.mail_id.res_id)
            _object_ids = comm.object_ids

        partner_id = tracking_email.partner_id.id
        if partner_id:
            self.env["partner.communication.job"].create(
                {
                    "config_id": _config_id.id,
                    "partner_id": partner_id,
                    "object_ids": _object_ids or partner_id,
                }
            )
        tracking_email.partner_id.message_post(
            body=_("The email couldn't be sent due to invalid address"),
            subject=tracking_email.name
        )

    @api.model
    def process_spam(self, tracking_email, metadata):
        tracking_email.partner_id.message_post(
            body=_("The email was marked as spam by the partner"),
            subject=tracking_email.name
        )
