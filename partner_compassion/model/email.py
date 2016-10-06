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
                if not (message.model == 'res.partner' and message.res_id ==
                        partner.id):
                    message_id = partner.message_post(
                        message.body, message.subject)
                    p_message = message.browse(message_id)
                    p_message.write({
                        'subtype_id': self.env.ref('mail.mt_comment').id,
                        'notified_partner_ids': [(4, partner.id)],
                        # Set parent to have the tracking working
                        'parent_id': message.id
                    })


class MailMessage(models.Model):
    """ Enable many thread notifications to track the same e-mail.
        It reads the parent_id of messages to do so.
    """
    _inherit = 'mail.message'

    @api.model
    def _message_read_dict_postprocess(self, messages, message_tree):
        res = super(MailMessage, self)._message_read_dict_postprocess(
            messages, message_tree)
        for message_dict in messages:
            mail_message_id = message_dict.get('id', False)
            if mail_message_id:
                # Add parent message ids in the search
                message_ids = [mail_message_id]
                message = self.browse(mail_message_id)
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
