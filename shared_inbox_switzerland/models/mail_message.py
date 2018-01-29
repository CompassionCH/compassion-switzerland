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


class MailMessage(models.Model):
    """
    Special handling of incoming messages in the info channel.
    When a user mark a message as done, remove it from inbox of all
    other users that are following the info channel, as the message is
    most probably treated.
    """
    _inherit = 'mail.message'

    @api.multi
    def set_message_done(self):
        info_channel = self.env.ref('shared_inbox_switzerland.info_inbox')
        super(MailMessage, self).set_message_done()
        info_messages = self.filtered(
            lambda m: info_channel.id in m.channel_ids.ids)
        other_notified_users = info_messages.mapped(
            'notification_ids.res_partner_id.user_ids') - self.env.user
        for user in other_notified_users:
            super(MailMessage, self.sudo(user)).set_message_done()
