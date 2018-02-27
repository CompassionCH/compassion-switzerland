# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api


class Attendee(models.Model):
    _inherit = 'calendar.attendee'

    @api.multi
    def _send_mail_to_attendees(self, template_xmlid, force_send=False):
        # only send email to compassion staff
        compassion_staff = self.filtered(
            lambda x: x.partner_id.user_ids and
            x.partner_id.user_ids[0].share is False)

        return super(Attendee, compassion_staff)._send_mail_to_attendees(
            template_xmlid, True)

    @api.multi
    def send_invitation_to_partner(self):
        return super(Attendee, self)._send_mail_to_attendees(
            'calendar.calendar_template_meeting_invitation', True)
