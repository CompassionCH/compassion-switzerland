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
                notify = message.model and not (
                    message.model == 'res.partner' and
                    message.res_id == partner.id
                )
                if notify:
                    p_message = partner.message_post(
                        email.body_html, email.subject)
                    p_message.write({
                        'subtype_id': self.env.ref('mail.mt_comment').id,
                        # Set parent to have the tracking working
                        'parent_id': message.id,
                        'author_id': message.author_id.id
                    })

            # Set Discussion in message
            # in order to display the tracking information in the
            # related object thread.
            if message.model:
                message_vals = {}
                if not message.subtype_id:
                    message_vals['subtype_id'] = self.env.ref(
                        'mail.mt_comment').id
                message.write(message_vals)


class EmailTemplate(models.Model):
    """ Remove functionality to search partners given the email_to field.
        This is not good behaviour for Compassion CH where we have
        some partners that share the same e-mail and because we won't
        create a new partner when sending to a static address
    """
    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids=None, fields=None):
        context = self.env.context.copy()
        if 'tpl_partners_only' in context:
            del context['tpl_partners_only']
        return super(EmailTemplate, self.with_context(
            context)).generate_email_batch(res_ids, fields=fields)
