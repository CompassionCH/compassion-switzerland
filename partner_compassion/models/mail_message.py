##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################


from odoo import models, api, fields


class MailMessage(models.Model):
    """ Enable many thread notifications to track the same e-mail.
        It reads the parent_id of messages to do so.
    """
    _inherit = 'mail.message'

    ancestor = fields.Many2one('mail.message', compute='_compute_ancestor')
    tracking_ids = fields.Many2many(
        'mail.message', 'mail_message_to_mail_message_tracking',
        'message_id', 'tracking_message_id',
        'Related tracked messages')

    @api.multi
    def _compute_ancestor(self):
        for message in self:
            previous = message
            ancestor = message.parent_id
            while ancestor:
                previous = ancestor
                ancestor = ancestor.parent_id
            message.ancestor = ancestor or previous

    def tracking_status(self):
        """
        Inherit from mail_tracking module to find tracking of parent and
        children messages.
        Useful to display tracking in thread of partner.
        :return: dict {message_id: [(status, tracking_id, partner_name,
                                    partner_id)]}
        """
        res = dict()
        for message in self:
            # if the message is not an email, it will not have a tracking
            # number.
            if message.message_type != "email" and message.subtype_id.name \
                    != "Discussions":
                res[message.id] = []
                continue
            search_messages = message
            parent = message.parent_id
            while parent:
                search_messages += parent
                parent = parent.parent_id
            search_messages += message.child_ids
            mess_results = super(MailMessage, search_messages).tracking_status()
            tracking = mess_results.get(message.id)
            if not tracking and len(mess_results) > 1:
                tracking_ids = list()
                for m_id, m_tracking in list(mess_results.items()):
                    if m_tracking:
                        for mm_tracking in m_tracking:
                            if mm_tracking[1] not in tracking_ids:
                                tracking.append(mm_tracking)
                                tracking_ids.append(mm_tracking[1])
            res[message.id] = tracking
        return res
