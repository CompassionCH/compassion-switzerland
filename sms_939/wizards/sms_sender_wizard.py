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
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


def smsbox_send(request, headers, config):
    server = config['server']
    port = config['port']
    endpoint = config['endpoint']
    request_server = httplib.HTTPConnection(server, port, timeout=10)
    url = endpoint + '?' + urllib.urlencode(request)
    _logger.info("Sending SMS message: %s", url)
    request_server.request('GET', url, headers=headers)
    response = request_server.getresponse()
    _logger.info("SMS response status: %s", response.status)
    _logger.debug(response.read())


class SmsSender(models.TransientModel):

    _name = 'sms.sender.wizard'
    _description = 'SMS sender wizard'

    subject = fields.Char()
    text = fields.Text()
    partner_id = fields.Many2one(
        'res.partner', 'Partner', compute='_compute_partner')
    sms_request_id = fields.Many2one(comodel_name='sms.child.request')
    sms_provider_id = fields.Many2one(
        'sms.provider', "SMS Provider",
        default=lambda self: self.env.ref('sms_939.large_account_id', False),
        readonly=False)

    @api.multi
    def _compute_partner(self):
        for wizard in self:
            wizard.partner_id = self.env.context.get('partner_id')
            if not wizard.partner_id:
                raise UserError(_("No valid partner"))

    @api.multi
    def send_sms(self, mobile):
        self.ensure_one()
        if not mobile:
            return False

        headers = {}
        username = self.sms_provider_id.username_939
        password = self.sms_provider_id.password_939
        auth = base64.encodestring('%s:%s' % (username,
                                              password)).replace('\n', '')
        headers['Authorization'] = 'Basic ' + auth
        request = [
            ('receiver', mobile),
            ('service', 'compassion'),
            ('maximumSMSAmount', 3),
            ('cost', 0),
            ('text', self.text.encode('utf8'))
        ]
        server_config = {'server': self.sms_provider_id.server_939,
                         'port': self.sms_provider_id.port_939,
                         'endpoint': self.sms_provider_id.endpoint_939}
        smsbox_send(request, headers, server_config)
        return True

    def send_sms_partner(self):

        if not self.partner_id or not self.partner_id.mobile:
            return False
        if self.send_sms(self.partner_id.mobile.replace(u'\xa0', u'')):
            self.partner_id.message_post(body=self.text,
                                         subject=self.subject,
                                         partner_ids=self.partner_id,
                                         type='comment')
            return True
        return False

    def send_sms_request(self):

        if not self.sms_request_id or not self.sms_request_id.sender:
            return False
        if self.send_sms(self.sms_request_id.sender.replace(u'\xa0', u'')):
            self.sms_request_id.message_post(body=self.text,
                                             subject=self.subject,
                                             type='comment')
            return True
        return False
