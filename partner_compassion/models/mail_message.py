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

    @api.model
    def _message_read_dict_postprocess(self, messages, message_tree):
        res = super(MailMessage, self)._message_read_dict_postprocess(
            messages, message_tree)
        for message_dict in messages:
            mail_message_id = message_dict.get('id', False)
            if mail_message_id:
                # Add parent and child message ids in the search
                message_ids = [mail_message_id]
                message = self.browse(mail_message_id)
                message_ids.extend(message.tracking_ids.ids or [])
                message_ids.extend(message.child_ids.ids)
                while message.parent_id:
                    message = message.parent_id
                    message_ids.append(message.id)

                # Code copied from mail_tracking module (be aware of updates)
                partner_trackings = {}
                for partner in message_dict.get('partner_ids', []):
                    partner_id = partner[0]
                    tracking_email = self.env['mail.tracking.email'].search([
                        ('mail_message_id', 'in', message_ids),
                        ('partner_id', '=', partner_id),
                    ], limit=1)
                    status = self._partner_tracking_status_get(tracking_email)
                    partner_trackings[str(partner_id)] = (
                        status, tracking_email.id)

            message_dict['partner_trackings'] = partner_trackings
        return res
