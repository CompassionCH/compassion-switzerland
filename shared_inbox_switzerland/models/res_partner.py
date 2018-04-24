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


from odoo import models, api


class ResPartner(models.Model):
    """
    This inheritance ensures that replies to the info channel are sent
    to the partner. It finds if the message sent is a reply to an existing
    message and in that case sends it to the partner.
    It also ensures that the user sending the message doesn't get subscribed
    to the mail_thread of the partner.
    """
    _inherit = 'res.partner'

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification',
                     subtype=None, parent_id=False, attachments=None,
                     content_subtype='html', **kwargs):
        reply = self.env.ref('shared_inbox_switzerland.reply_inbox')
        channel_ids = kwargs.get('channel_ids', [(0, 0, [0])])[0][2]
        is_email_reply = reply.id in channel_ids
        # Find if the message is a reply of user to partner message
        if subtype == 'mail.mt_comment' and subject and not is_email_reply:
            parent = self.message_ids.filtered(
                lambda m: m.author_id == self and m.subject and
                m.subject in subject)
            if parent:
                # include previous message at the bottom of the email
                parent_id = parent[0].id
                kwargs['partner_ids'] = [(6, 0, self.ids)]
                reply_quote = u'\r\n<br/>\r\n<br/>\r\n<br/>' \
                    u'-------------' \
                    u'\r\n<br/>' \
                    u'Email from: {}' \
                    u'\r\n<br/>' \
                    u'Date: {}' \
                    u'\r\n<br/>' \
                    u'Subject: {}' \
                    u'\r\n<br/>\r\n<br/>{}'.format(
                        parent[0].email_from,
                        parent[0].date,
                        parent[0].subject,
                        parent[0].body
                    )
                try:
                    body = unicode(
                        body.decode('utf-8')) if 'utf-8' in body else body
                    body += reply_quote
                except UnicodeEncodeError:
                    body += reply_quote

        message = super(ResPartner, self.with_context(
            # Disable autosubscription
            mail_create_nosubscribe=True)).message_post(
            body=body, subject=subject, message_type=message_type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            content_subtype=content_subtype, **kwargs)
        if is_email_reply:
            # Notifiy Odoo author of previous message
            message.parent_id.author_id._notify_by_email(
                message, force_send=True)
        return message

    def create(self, vals):
        return super(ResPartner, self.with_context(
            mail_create_nosubscribe=True)).create(vals)

    @api.model
    def _notify_prepare_email_values(self, message):
        """
        Always put reply_to value in mail notifications.
        :param message: the message record
        :return: mail values
        """
        mail_values = super(ResPartner,
                            self)._notify_prepare_email_values(message)

        # Find reply-to in mail template.
        base_template = None
        if message.model and self._context.get('custom_layout', False):
            base_template = self.env.ref(self._context['custom_layout'],
                                         raise_if_not_found=False)
        if not base_template:
            base_template = self.env.ref(
                'mail.mail_template_data_notification_email_default')

        if base_template.reply_to:
            mail_values['reply_to'] = base_template.reply_to

        return mail_values
