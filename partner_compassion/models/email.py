# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

from sendgrid import SendGridAPIClient

from openerp import models, api
from openerp.exceptions import Warning
from openerp.tools.config import config


class Email(models.Model):
    """ Email message sent through SendGrid """
    _inherit = 'mail.mail'

    @api.multi
    def send_sendgrid(self):
        """ Post the message in partner, with tracking.
        """
        super(Email, self).send_sendgrid()
        for email in self:
            message = email.mail_message_id
            for partner in email.recipient_ids:
                notify = message.model and not (
                    message.model == 'res.partner' and
                    message.res_id == partner.id
                ) and message.model != 'mail.notification'
                if notify:
                    message_id = partner.message_post(
                        email.body_html, email.subject)
                    p_message = message.browse(message_id)
                    p_message.write({
                        'subtype_id': self.env.ref('mail.mt_comment').id,
                        'notified_partner_ids': [(4, partner.id)],
                        # Set parent to have the tracking working
                        'parent_id': message.id,
                        'author_id': message.author_id.id
                    })

            # Set notified partners and type Discussion in message
            # in order to display the tracking information in the
            # related object thread. (Except for notifications which are
            # already tracked)
            enable_tracking = message.model and message.model \
                != 'mail.notification'
            if enable_tracking:
                message_vals = {}
                if not message.subtype_id:
                    message_vals['subtype_id'] = self.env.ref(
                        'mail.mt_comment').id
                if not message.notified_partner_ids:
                    message_vals['notified_partner_ids'] = [
                        (6, 0, email.recipient_ids.ids)]
                message.write(message_vals)


class EmailTemplate(models.Model):
    """ Remove functionality to search partners given the email_to field.
        This is not good behaviour for Compassion CH where we have
        some partners that share the same e-mail and because we won't
        create a new partner when sending to a static address
    """
    _inherit = 'email.template'

    @api.v7
    def generate_email_batch(self, cr, uid, tpl_id=False, res_ids=None,
                             fields=None, context=None):
        if context and 'tpl_partners_only' in context:
            del context['tpl_partners_only']
        return super(EmailTemplate, self).generate_email_batch(
            cr, uid, tpl_id, res_ids, fields=fields, context=context)


class TrackingEvent(models.Model):
    _inherit = 'mail.tracking.event'

    @api.model
    def process_unsub(self, tracking_email, metadata):
        """
        Opt out partners when they unsubscribe from Sendgrid.
        Remove unsub from Sendgrid
        :param tracking_email:
        :param metadata:
        :return:
        """
        tracking_email.partner_id.opt_out = True
        tracking_email.partner_id.message_post(
            "Partner Unsubscribed from marketing e-mails", "Opt-out")
        api_key = config.get('sendgrid_api_key')
        if not api_key:
            raise Warning(
                'ConfigError',
                'Missing sendgrid_api_key in conf file')

        sg = SendGridAPIClient(apikey=api_key)
        sg.client.suppression.unsubscribes._(tracking_email.recipient).delete()
        return super(TrackingEvent, self).process_unsub(
            tracking_email, metadata)
