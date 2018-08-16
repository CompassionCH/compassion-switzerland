# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nathan Fluckiger <nathan.fluckiger@hotmail.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import httplib
import urllib

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.config import config


class SmsSender(models.TransientModel):

    _name = 'sms.sender.wizard'
    _description = 'SMS sender wizard'

    subject = fields.Char()
    text = fields.Text()
    partner_id = fields.Many2one(
        'res.partner', 'Partner', compute='_compute_partner')

    @api.multi
    def _compute_partner(self):
        for wizard in self:
            wizard.partner_id = self.env.context.get('partner_id')
            if not wizard.partner_id:
                raise UserError(_("No valid partner"))

    @api.multi
    def send_sms(self):
        self.ensure_one()
        if not self.partner_id.mobile:
            return False

        headers = {}
        username = config.get('939_username')
        password = config.get('939_password')

        request_server = httplib.HTTPConnection(
            'blue.smsbox.ch', 10020, timeout=10)

        auth = base64.encodestring('%s:%s' % (username,
                                              password)).replace('\n', '')

        headers['Authorization'] = 'Basic ' + auth

        request = [
            ('receiver', self.partner_id.mobile.replace(u'\xa0', u'')),
            ('service', 'compassion'),
            ('cost', 0),
            ('text', self.text)
        ]
        request_server.request('GET', '/Blue/sms/rest/user/websend?'
                               + urllib.urlencode(request), headers=headers)
        self.partner_id.message_post(body=self.text,
                                     subject=self.subject,
                                     partner_ids=self.partner_id,
                                     type='comment')
        return True
