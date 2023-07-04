##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models, fields
from odoo.tools import email_split


class Email(models.Model):
    _inherit = "mail.mail"

    # Shortcut to mail tracking events
    tracking_event_ids = fields.One2many(
        related="mail_tracking_ids.tracking_event_ids", readonly=True
    )

    def send(self, auto_commit=False, raise_exception=False):
        """
        Prevents deleting emails for better control.
        Sends a CC to all linked contacts that have option activated.
        """
        self.write({"auto_delete": False})
        for mail in self:
            cc = mail.recipient_ids.mapped("other_contact_ids").filtered("email_copy")
            email_cc = []
            if cc:
                email_cc = email_split(mail.email_cc or "")
                email_cc.extend(cc.mapped("email"))
            mail.email_cc = ";".join(email_cc)
        return super().send(auto_commit, raise_exception)


class EmailTemplate(models.Model):
    """Remove functionality to search partners given the email_to field.
    This is not good behaviour for Compassion CH where we have
    some partners that share the same e-mail and because we won't
    create a new partner when sending to a static address
    """

    _inherit = "mail.template"

    def generate_email(self, res_ids=None, fields=None):
        context = self.env.context.copy()
        if "tpl_partners_only" in context:
            del context["tpl_partners_only"]
        return super(EmailTemplate, self.with_context(context)).generate_email(
            res_ids, fields=fields
        )
