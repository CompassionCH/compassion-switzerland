##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo import api, models

logger = logging.getLogger(__name__)


class SmsChildRequest(models.Model):
    _inherit = 'sms.child.request'

    @api.multi
    def send_step2_reminder(self):
        """
        Sends a reminder to people that didn't complete step 2
        :return: True
        """
        communication_config = self.env.ref(
            'partner_communication_switzerland.sms_registration_reminder')
        for request in self:
            request.sponsorship_id.send_communication(communication_config)
        return True
