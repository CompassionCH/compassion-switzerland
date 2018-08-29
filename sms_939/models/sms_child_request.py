# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import api, models, _


class SmsRequest(models.Model):
    _inherit = 'sms.child.request'

    @api.multi
    def send_step1_reminder(self):
        """ Sends SMS reminder using 939 API """
        self.ensure_one()
        sms_sender = self.env['sms.sender.wizard'].create({
            'sms_request_id': self.id,
            'text': _(
                u"Thank you for your wish to sponsor a child through "
                u"Compassion. Take a moment today to change the life of "
                u"%s: %s"
            ) % (self.child_id.preferred_name or _("this child"),
                 self.full_url),
            'subject': _("SMS sponsorship reminder")
        })
        sms_sender.send_sms_request()
        super(SmsRequest, self).send_step1_reminder()
