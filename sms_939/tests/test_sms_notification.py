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
import urllib.request
import urllib.parse
import urllib.error
import mock
from requests import ReadTimeout

from odoo.fields import Datetime
from odoo.tests import HttpCase

_logger = logging.getLogger(__name__)


class TestMobileAppConnector(HttpCase):

    def setUp(self):
        super().setUp()
        self.env['ir.config_parameter'] \
            .set_param('web.external.url', 'base')
        external_url = self.env['ir.config_parameter'] \
            .get_param('web.external.url')
        self.assertEqual(external_url, 'base')

    def _send_sms_notification(self, params, send_mode='request'):
        uuid = 'uid-1232389'
        params.update({
            'instance': 'test',
            'sender': '+41414104141',
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
            url_params = urllib.parse.urlencode(params)
            try:
                response = self.url_open('/sms/mnc/?' + url_params, timeout=1)
                response_str = response.read()
                return response_str
            except ReadTimeout:
                print("Timeout occured")

        notification = self.env['sms.notification'].create(params)
        self.assertEqual(notification.state, 'new')
        notification.run_service()
        return notification

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_controller(self, smsbox_send):
        self._send_sms_notification({
            'service': 'test',
            'language': 'en',
            'text': 'This is a fake message'
        })
        self.assertIn(b'Thanks!', self._get_sms_message(smsbox_send))

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_basic_service(self, smsbox_send):
        notification = self._send_sms_notification({
            'service': 'test',
            'language': 'fr',
            'text': 'This is a fake message'
        }, send_mode='direct')

        self.assertEqual(notification.state, 'success')
        self.assertEqual(notification.language, 'fr_CH')
        self.assertTrue(b'Thanks!' in self._get_sms_message(smsbox_send))

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_sms_notification__with_unknown_hook(self, smsbox_send):
        self._send_sms_notification({
            'service': 'wrong_service',
            'language': 'en',
            'text': 'This is a fake message'
        })

        self.assertIn(b'Sorry, we could not understand your request. '
                      b'Supported services are',
                      self._get_sms_message(smsbox_send))

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_sms_notification__test_translation(self, smsbox_send):
        self._send_sms_notification({
            'service': 'wrong_service',
            'language': 'fr',
            'text': 'This is a fake message'
        })

        self.assertIn(
            b'COMPASSION- COMPASSIONDE- COMPASSIONIT- COMPASSIONEN- TEST- TESTERROR',
            self._get_sms_message(smsbox_send))

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_sms_notification__test_mode(self, smsbox_send):
        self._send_sms_notification({
            'service': 'wrong_service',
            'language': 'fr',
            'text': 'This is a test'
        })

        self.assertFalse(smsbox_send.called)

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_sms_notification__raising_exception(self, smsbox_send):
        self._send_sms_notification({
            'service': 'testerror',
            'language': 'en'
        })

        self.assertIn(b'Sorry, the service is not available',
                      self._get_sms_message(smsbox_send))

    @mock.patch('odoo.addons.sms_939.wizards.sms_sender_wizard.smsbox_send')
    def test_sponsor_service(self, smsbox_send):
        response = self._send_sms_notification({
            'language': 'fr',
            'service': 'compassion'
        }, send_mode='request')

        self.assertIn("Thank you for your will to help a child !", response.answer)
        self.assertRegex(str(self._get_sms_message(smsbox_send)),
                         r'this link: http://localhost:8069/r/\w')

    def _get_sms_message(self, smsbox_send):
        self.assertTrue(smsbox_send.called)
        sms_args = smsbox_send.call_args[0][0]
        return next(pair[1] for pair in sms_args if pair[0] == 'text')
