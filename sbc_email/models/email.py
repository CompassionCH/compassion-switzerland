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
        """ Post the message in partner.
        """
        super(Email, self).send_sendgrid()
        for email in self:
            message = email.mail_message_id
            for partner in email.recipient_ids:
                partner.message_post(message.body, message.subject)
