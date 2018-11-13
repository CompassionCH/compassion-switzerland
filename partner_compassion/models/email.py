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
from odoo import models, api

_logger = logging.getLogger(__name__)

try:
    from sendgrid.helpers.mail import Email as SendgridEmail
except ImportError:
    _logger.warning("Please install Sendgrid for partner_compassion")


class Email(models.Model):
    """ Email message sent through SendGrid """
    _inherit = 'mail.mail'

    @api.multi
    def send_sendgrid(self):
        """ Post the message in partner, with tracking.
        """
        self.filtered(lambda e: e.state == 'outgoing').write({
            'auto_delete': False})
        super(Email, self).send_sendgrid()
        for email in self:
            message = email.mail_message_id
            for partner in email.recipient_ids:
                notify = message.model and not (
                    message.model == 'res.partner' and
                    message.res_id == partner.id
                )
                if notify:
                    p_message = partner.message_post(
                        email.body_html, email.subject)
                    p_message.write({
                        'subtype_id': self.env.ref('mail.mt_comment').id,
                        # Set parent to have the tracking working
                        'parent_id': message.id,
                        'author_id': message.author_id.id
                    })

    @api.multi
    def _prepare_sendgrid_data(self):
        """
        Sends a CC to all linked contacts that have option activated.
        """
        s_mail = super(Email, self)._prepare_sendgrid_data()
        email_cc = self.email_cc or ''
        for recipient in self.recipient_ids.filtered(
                'other_contact_ids.email_copy'):
            for personalization in s_mail._personalizations:
                for to in personalization._tos:
                    if recipient.email == to['email']:
                        for cc in recipient.other_contact_ids.filtered(
                                'email_copy'):
                            personalization.add_cc(SendgridEmail(cc.email))
                            email_cc += ';' + cc.email
        self.email_cc = email_cc.strip(';')
        return s_mail


class EmailTemplate(models.Model):
    """ Remove functionality to search partners given the email_to field.
        This is not good behaviour for Compassion CH where we have
        some partners that share the same e-mail and because we won't
        create a new partner when sending to a static address
    """
    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids=None, fields=None):
        context = self.env.context.copy()
        if 'tpl_partners_only' in context:
            del context['tpl_partners_only']
        return super(EmailTemplate, self.with_context(
            context)).generate_email(res_ids, fields=fields)
