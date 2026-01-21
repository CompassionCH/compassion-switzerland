##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import fields, models
from odoo.tools import email_split


class Email(models.Model):
    _inherit = "mail.mail"

    # Shortcut to mail tracking events
    tracking_event_ids = fields.One2many(
        related="mail_tracking_ids.tracking_event_ids", readonly=True
    )

    def send(self, auto_commit=False, raise_exception=False, post_send_callback=None):
        """
        Prevents deleting emails for better control.
        Sends a CC to all linked contacts that have option activated.
        """
        self.write({"auto_delete": False})
        for mail in self:
            cc = mail.recipient_ids.mapped("child_ids").filtered("email_copy")
            email_cc = []
            if cc:
                email_cc = email_split(mail.email_cc or "")
                email_cc.extend(cc.mapped("email"))
            mail.email_cc = ";".join(email_cc)
        return super().send(auto_commit, raise_exception, post_send_callback)
