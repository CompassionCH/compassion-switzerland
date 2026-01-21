##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models


class Attendee(models.Model):
    _inherit = "calendar.attendee"

    def _send_mail_to_attendees(self, mail_template, force_send=False):
        # Only send email to compassion staff
        compassion_staff = self.filtered(
            lambda x: x.partner_id.user_ids and not x.partner_id.user_ids[0].share
        )

        return super(Attendee, compassion_staff)._send_mail_to_attendees(
            mail_template, force_send
        )
