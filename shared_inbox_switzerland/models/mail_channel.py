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


class MailChannel(models.Model):
    """
    Special handling of incoming messages in the info channel.
    Post message on partner and notify members of the channel.
    """
    _inherit = 'mail.channel'

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification',
                     subtype=None, parent_id=False, attachments=None,
                     content_subtype='html', **kwargs):
        message = super(MailChannel, self).message_post(
            body=body, subject=subject, message_type=message_type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            content_subtype=content_subtype, **kwargs)
        info = self.env.ref('shared_inbox_switzerland.info_inbox')
        if self == info:
            author = message.author_id
            # Post message on partner and notify channel members.
            message.write({
                'model': 'res.partner',
                'res_id': author.id,
                'partner_ids': [(6, 0, self.channel_partner_ids.ids)]
            })
            message._notify()
        return message


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    @api.returns('self', lambda value: value.id)
    def message_post(self, body='', subject=None, message_type='notification',
                     subtype=None, parent_id=False, attachments=None,
                     content_subtype='html', **kwargs):
        # Find if the message is a reply to partner message
        if subtype == 'mail.mt_comment' and subject and 'info' in subject:
            parent = self.message_ids.filtered(
                lambda m: m.author_id == self and m.subject)
            if parent:
                parent_id = parent[0].id
                subject = subject.replace('info', parent[0].subject)
                kwargs['partner_ids'] = [(6, 0, self.ids)]
        message = super(ResPartner, self.with_context(
            # Disable autosubscription
            mail_create_nosubscribe=True)).message_post(
            body=body, subject=subject, message_type=message_type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            content_subtype=content_subtype, **kwargs)
        return message
