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
from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import api, models, fields, _


class SmsRequest(models.Model):
    _inherit = 'sms.child.request'

    def complete_step1(self, sponsorship_id):
        """
        Mark partner to validate if it was newly created.
        :param sponsorship_id: new sponsorship
        :return: True
        """
        self.ensure_one()
        if self.new_partner:
            self.partner_id.state = 'pending'
        return super(SmsRequest, self).complete_step1(sponsorship_id)

    @api.multi
    def send_step1_reminder(self):
        """ Sends SMS reminder using 939 API """
        self.ensure_one()
        one_day_ago = date.today() - relativedelta(days=1)
        completed_requests = self.search([
            ('date', '<', fields.Date.today()),
            ('date', '>=', fields.Date.to_string(one_day_ago)),
            ('state', 'in', ['step1', 'step2']),
        ]).filtered(lambda r: r.sender == self.sender)
        if not completed_requests:
            sms_sender = self.env['sms.sender.wizard'].create({
                'sms_request_id': self.id,
                'text': _(
                    u"Thank you for your interest to sponsor a child with "
                    u"Compassion. Why don't you take a moment today to change "
                    u"the life of %s? %s"
                ) % (self.child_id.preferred_name or _("this child"),
                     self.full_url),
                'subject': _("SMS sponsorship reminder")
            })
            sms_sender.send_sms_request()
        super(SmsRequest, self).send_step1_reminder()
