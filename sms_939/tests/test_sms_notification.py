# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
import time
import urllib
import mock
from odoo.fields import Datetime
from odoo.tests import HttpCase
from xml.etree import ElementTree

_logger = logging.getLogger(__name__)


class TestMobileAppConnector(HttpCase):

    def setUp(self):
        super(TestMobileAppConnector, self).setUp()
        self.env['ir.config_parameter'] \
            .set_param('web.external.url', 'base')
        external_url = self.env['ir.config_parameter'] \
            .get_param('web.external.url')
        self.assertEqual(external_url, 'base')

    def _send_sms_notification(self, params, send_mode='direct'):
        uuid = 'uid-1232389'
        params.update({
            'instance': 'test',
            'sender': '+41789364595',
            'operator': 'orange',
            'command': 'FORWARD',
            'date': Datetime.now(),
            'uuid': uuid,
        })
        if send_mode != 'direct':
            params.update({
                'receptionDate': Datetime.now(),
                'requestUid': uuid,
            })
            url_params = urllib.urlencode(params)
            response = self.url_open('/sms/mnc/?' + url_params)
            response_str = response.read()
            return response_str

        notification = self.env['sms.notification'].create(params)
        self.assertEqual(notification.state, 'new')
        response = notification.run_service()
        response_str = response.data
        self.assertEqual(notification.answer, response_str)
        return notification

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_controller(self, smsbox_send):
        smsbox_send.side_effect = _logger.info("sms sent")
        response = self._send_sms_notification({
            'service': 'test',
            'language': 'en',
            'text': 'This is a test'
        }, send_mode='request')
        self.assertIn('Thanks!', response)

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_basic_service(self, smsbox_send):
        smsbox_send.side_effect = _logger.info("sms sent")
        notification = self._send_sms_notification({
            'service': 'test',
            'language': 'fr',
            'text': 'This is a test'
        })
        self.assertEqual(notification.state, 'success')
        self.assertEqual(notification.language, 'fr_CH')
        self.assertTrue('Thanks!' in notification.answer)

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_sms_notification__with_unknown_hook(self, smsbox_send):
        # smsbox_send.side_effect = _logger.info("sms sent")
        response = self._send_sms_notification({
            'service': 'wrong_service',
            'language': 'en',
            'text': 'This is a test'
        }, send_mode='request')
        while not smsbox_send.called:
            print self.env['queue.job'].search([])
            time.sleep(1)
        self.assertIn('Sorry, we could not understand your request. '
                      'Supported services are', response)

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_sms_notification__test_translation(self, smsbox_send):
        smsbox_send.side_effect = _logger.info("sms sent")
        response = self._send_sms_notification({
            'service': 'wrong_service',
            'language': 'fr',
            'text': 'This is a test'
        }, send_mode='request')
        self.assertIn('Les services', response)

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_sms_notification__raising_exception(self, smsbox_send):
        smsbox_send.side_effect = _logger.info("sms sent")
        response = self._send_sms_notification({
            'service': 'testerror',
            'language': 'en'
        }, send_mode='request')
        self.assertIn('Sorry, the service is not available', response)

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_sponsor_service(self, smsbox_send):
        smsbox_send.side_effect = _logger.info("sms sent")
        response = self._send_sms_notification({
            'language': 'fr',
            'service': 'compassion'
        }, send_mode='request')

        message = ElementTree.fromstring(response) \
            .find('./message/text') \
            .text.replace('\n', '')
        self.assertRegexpMatches(
            message,
            r'^Merci pour votre .*? en cliquant sur ce lien : '
            r'http://localhost:8069/r/\w+$')
