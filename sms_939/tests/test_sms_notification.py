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
import urllib
from odoo.fields import Datetime
from odoo.tests import HttpCase

_logger = logging.getLogger(__name__)


class TestMobileAppConnector(HttpCase):

    def _send_sms_notification(self, params, send_mode='direct'):
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

    def test_controller(self):
        response = self._send_sms_notification({
            'service': 'test',
            'language': 'fr',
            'text': 'This is a test'
        }, send_mode='request')
        self.assertIn('Thanks!', response)

    def test_basic_service(self):
        notification = self._send_sms_notification({
            'service': 'test',
            'language': 'fr',
            'text': 'This is a test'
        })
        self.assertEqual(notification.state, 'success')
        self.assertTrue('Thanks!' in notification.answer)
