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
from odoo.exceptions import UserError
from odoo.tools.config import config

_logger = logging.getLogger(__name__)

try:
    from sendgrid import SendGridAPIClient
    from python_http_client import NotFoundError
except ImportError:
    _logger.warning("Please install sendgrid and python_http_client")


class MailTrackingEvent(models.Model):
    _inherit = "mail.tracking.event"

    @api.model
    def process_delivered(self, tracking_email, metadata):
        """ Mark correspondence as read. """
        correspondence = self.env['correspondence'].search([
            ('email_id', '=', tracking_email.mail_id.id),
            ('letter_delivered', '=', False)
        ])
        correspondence.write({
            'letter_delivered': True
        })
        return super().process_delivered(
            tracking_email, metadata)

    def send_mails_to_partner_and_staff(self, tracking_email, metadata,
                                        staff_email_body):
        partner = tracking_email.partner_id
        if partner:
            self._invalid_email(tracking_email)
            to_write = {
                'invalid_mail': partner.email,
                'email': False
            }

            staff_ids = self.env['res.config.settings'].sudo().get_param(
                'invalid_mail_notify_ids')
            del to_write['email']
            subject = _('Email invalid! An error occurred: '
                        + metadata.get('error_type'))
            body = _(staff_email_body)
            partner.message_post(body=body,
                                 subject=subject,
                                 partner_ids=staff_ids,
                                 type='comment', subtype='mail.mt_comment',
                                 content_subtype='plaintext')
            partner.write(to_write)

    def _remove_address_from_sendgrid_bounce_list(self, tracking_email):
        tracking_email.partner_id.message_post(
            _('The email was bounced and not delivered to the partner'),
            tracking_email.name)
        self._get_sendgrid().client.suppression.bounces._(
            tracking_email.recipient).delete()

    @api.model
    def process_hard_bounce(self, tracking_email, metadata):
        body = 'Warning : Sponsor\'s Email is invalid!\nError description: ' \
               + metadata.get('error_description')
        self.send_mails_to_partner_and_staff(tracking_email, metadata, body)
        return super().process_hard_bounce(
            tracking_email, metadata)

    @api.model
    def process_soft_bounce(self, tracking_email, metadata):
        body = _('Warning : Sponsor\'s Email is invalid!\n Error description: '
                 + metadata.get('error_description'))
        self.send_mails_to_partner_and_staff(tracking_email, metadata, body)
        return super().process_soft_bounce(
            tracking_email, metadata)

    @api.model
    def process_unsub(self, tracking_email, metadata):
        """
        Opt out partners when they unsubscribe from Sendgrid.
        Remove unsub from Sendgrid
        """
        tracking_email.partner_id.opt_out = True
        tracking_email.partner_id.message_post(
            _('Partner Unsubscribed from marketing e-mails'), _("Opt-out"))
        sg = self._get_sendgrid()
        try:
            sg.client.suppression.unsubscribes._(
                tracking_email.recipient).delete()
        finally:
            return super().process_unsub(
                tracking_email, metadata)

    @api.model
    def process_reject(self, tracking_email, metadata):
        body = _('Warning : There is a problem with this Sponsor\'s Email. \n'
                 'reason: ' + metadata.get('error_type'))
        self.send_mails_to_partner_and_staff(tracking_email, metadata, body)

        return super().process_reject(tracking_email, metadata)

    def _invalid_email(self, tracking_email):
        """
        Sends invalid e-mail communication.
        """
        invalid_comm = self.env.ref(
            'partner_communication_switzerland.wrong_email')
        partner_id = tracking_email.partner_id.id
        if partner_id:
            self.env['partner.communication.job'].create({
                'config_id': invalid_comm.id,
                'partner_id': partner_id,
                'object_ids': partner_id,
            })
        tracking_email.partner_id.message_post(
            _('The email couldn\'t be sent due to invalid address'),
            tracking_email.name)
        try:
            self._get_sendgrid().client.suppression.invalid_emails._(
                tracking_email.recipient).delete()
            found = True
        except NotFoundError:
            try:
                self._get_sendgrid().client.suppression.blocks._(
                    tracking_email.recipient).delete()
                found = True
            except NotFoundError:
                try:
                    self._remove_address_from_sendgrid_bounce_list(tracking_email)
                    found = True
                except NotFoundError:
                    found = False
        if found:
            _logger.info("The recipient was removed from the Sendgrid supression lists")
        else:
            _logger.error("The recipient is not in the supression lists of sendgrid.")

    @api.model
    def process_spam(self, tracking_email, metadata):
        tracking_email.partner_id.message_post(
            _('The email was marked as spam by the partner'),
            tracking_email.name)
        self._get_sendgrid().client.suppression.spam_reports.delete(
            request_body={"emails": [tracking_email.recipient]})

    def _get_sendgrid(self):
        api_key = config.get('sendgrid_api_key')
        if not api_key:
            raise UserError(
                _('ConfigError'),
                _('Missing sendgrid_api_key in conf file'))

        return SendGridAPIClient(apikey=api_key)
