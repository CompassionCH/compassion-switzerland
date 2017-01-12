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


from openerp import models, api


class MailNotification(models.Model):
    _inherit = 'mail.notification'

    @api.multi
    def _notify_email(self, message_id, force_send=True, user_signature=True):
        """ Always send notifications by e-mail. Put parent_id in messages
        in order to enable tracking from the thread.
        """
        mail_ids = super(MailNotification, self)._notify_email(
            message_id, force_send, user_signature)
        if isinstance(mail_ids, list):
            flat_ids = [id for sublist in mail_ids for id in sublist]
            emails = self.env['mail.mail'].browse(flat_ids)
            tracking_ids = emails.mapped('mail_message_id')
            # Remove parent message from tracking messages to avoid having
            # duplicates in mail threads
            tracking_ids.write({'parent_id': False})
            message = self.env['mail.message'].browse(message_id)
            m_vals = {
                'tracking_ids': [(4, t.id) for t in tracking_ids]
            }
            # If message is coming from nowhere (direct e-mails)
            # post it on thread of partner
            if not message.model and not message.res_id:
                author = message.author_id
                recipients = message.partner_ids
                partner_thread = False
                if author.user_ids.filtered(lambda u: not u.share):
                    # Author is a Odoo user
                    partner_thread = recipients[0]
                elif author:
                    # Author is a partner
                    partner_thread = author
                if partner_thread:
                    m_vals.update({
                        'model': 'res.partner',
                        'res_id': partner_thread.id,
                        'record_name': partner_thread.name
                    })
            message.write(m_vals)
            emails.send()
        return mail_ids
