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
        reply = self.env.ref('shared_inbox_switzerland.reply_inbox')
        if self in info | reply:
            # Notify info channel members
            vals = {
                'partner_ids': [(6, 0, info.channel_partner_ids.ids)]
            }
            author = message.author_id
            if author:
                if not author.active and author.contact_id:
                    author = author.contact_id
                # Post message on partner.
                vals.update({
                    'model': 'res.partner',
                    'res_id': author.id,
                    'record_name': message.subject,
                })
            message.write(vals)
            message._notify()
        return message
