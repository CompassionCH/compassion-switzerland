
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
        """ Avoid to delete the e-mails sent.
        """
        self.filtered(lambda e: e.state == 'outgoing').write({
            'auto_delete': False})
        super().send_sendgrid()

    @api.multi
    def _prepare_sendgrid_data(self):
        """
        Sends a CC to all linked contacts that have option activated.
        """
        s_mail = super()._prepare_sendgrid_data()
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
        return super(self.with_context(
            context)).generate_email(res_ids, fields=fields)
