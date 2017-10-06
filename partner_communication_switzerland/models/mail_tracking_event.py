# -*- coding: utf-8 -*-
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
except ImportError:
    _logger.warning("Please install sendgrid.")


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
        return super(MailTrackingEvent, self).process_delivered(
            tracking_email, metadata)

    @api.model
    def process_unsub(self, tracking_email, metadata):
        """
        Opt out partners when they unsubscribe from Sendgrid.
        Remove unsub from Sendgrid
        """
        tracking_email.partner_id.opt_out = True
        tracking_email.partner_id.message_post(
            "Partner Unsubscribed from marketing e-mails", "Opt-out")
        sg = self._get_sendgrid()
        try:
            sg.client.suppression.unsubscribes._(
                tracking_email.recipient).delete()
        finally:
            return super(MailTrackingEvent, self).process_unsub(
                tracking_email, metadata)

    @api.model
    def process_reject(self, tracking_email, metadata):
        partner = tracking_email.partner_id
        if metadata.get('error_type') == 'Invalid' and 'RBL' not in \
                metadata.get('error_description', '') and not partner.user_ids:
            self._invalid_email(tracking_email)
            partner.email = False
        return super(MailTrackingEvent, self).process_reject(
            tracking_email, metadata)

    @api.model
    def process_hard_bounce(self, tracking_email, metadata):
        if not tracking_email.partner_id.user_ids:
            self._invalid_email(tracking_email)
            tracking_email.partner_id.email = False
        return super(MailTrackingEvent, self).process_hard_bounce(
            tracking_email, metadata)

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

    def _get_sendgrid(self):
        api_key = config.get('sendgrid_api_key')
        if not api_key:
            raise UserError(
                _('ConfigError'),
                _('Missing sendgrid_api_key in conf file'))

        return SendGridAPIClient(apikey=api_key)
