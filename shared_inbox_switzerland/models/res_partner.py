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
        new_body = body

        # Find if the message is a reply to partner message
        if subtype == 'mail.mt_comment' and subject:
            parent = self.message_ids.filtered(
                lambda m: m.author_id == self and m.subject and
                m.subject in subject)
            if parent:
                parent_id = parent[0].id
                kwargs['partner_ids'] = [(6, 0, self.ids)]
                # include previous message at the bottom of the email
                new_body += '\r\n<br/>\r\n<br/>\r\n<br/>'
                new_body += '-------------'
                new_body += '\r\n<br/>'
                new_body += 'Email from: '
                new_body += parent[0].email_from
                new_body += '\r\n<br/>'
                new_body += 'Date: '
                new_body += parent[0].date
                new_body += '\r\n<br/>'
                new_body += 'Subject: '
                new_body += parent[0].subject
                new_body += '\r\n<br/>\r\n<br/>'
                new_body += parent[0].body
        message = super(ResPartner, self.with_context(
            # Disable autosubscription
            mail_create_nosubscribe=True)).message_post(
            body=new_body, subject=subject, message_type=message_type,
            subtype=subtype, parent_id=parent_id, attachments=attachments,
            content_subtype=content_subtype, **kwargs)
        return message

    def create(self, vals):
        return super(ResPartner, self.with_context(
            mail_create_nosubscribe=True)).create(vals)
