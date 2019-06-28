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

from random import randint
from odoo import api, models, fields, _
from odoo.addons.queue_job.job import job, related_action


class SmsRequest(models.Model):
    _inherit = 'sms.child.request'

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

    @job(default_channel='root.sms_request')
    @related_action(action='related_action_sms_request')
    def reserve_child(self):
        self.ensure_one()
        if not self.event_id:
            res = self._take_child_from_website()
            if res:
                return res
        return super(SmsRequest, self).reserve_child()

    def _take_child_from_website(self):
        """ Search in the website child.
        """
        selected_children = self.env['compassion.child'].search(
            [('state', '=', 'I')]
        )
        if self.has_filter:
            selected_children = selected_children.filtered(
                self.check_child_parameters)

        if selected_children:
            # Take a random child among the selection
            index = randint(0, len(selected_children) - 1)
            child = selected_children[index]
            self.write({
                'child_id': child.id,
                'state': 'child_reserved'
            })
            child.hold_id.sms_request_id = self.id
            child.remove_from_wordpress()
            child.write({
                'state': 'S'
            })

            return True
        return False

    def cancel_request(self):
        if not self.event_id:
            self.child_id.write({'state': 'N'})
            self.child_id.add_to_wordpress()
        return super(SmsRequest, self).cancel_request()
