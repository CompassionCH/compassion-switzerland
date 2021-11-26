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
    _inherit = "calendar.attendee"

    @api.multi
    def _send_mail_to_attendees(self, template_xmlid):
        pass

    @api.multi
    def send_invitation_to_partner(self):
        pass
