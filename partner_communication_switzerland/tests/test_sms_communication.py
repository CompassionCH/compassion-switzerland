##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo.tests import TransactionCase
from mock import patch

logger = logging.getLogger(__name__)


class TestSponsorship(TransactionCase):
    """
    This will test related functionalities with SMS communications.
    """

    @patch('odoo.addons.sms_939.models.sms_api.SmsApi._smsbox_send')
    def test_sms_replacement_text(self, sms_send_mock):
        """
        Test that the communication text is well shortened for a SMS
        communication.
        """
        partner = self.env.ref('base.res_partner_1')
        partner.write({'mobile': partner.phone})
        config = self.env.ref('partner_communication.test_communication')
        sms_send_mock.return_value = True
        communication = self.env['partner.communication.job'].create({
            'partner_id': partner.id,
            'config_id': config.id,
            'send_mode': 'sms',
            'body_html': """
                        <h1>A communication example</h1>
                        <p>This is a great example showing that <a href="http://test">
                        testing is fun</a>.
                        </p>
                        <br/>
                        <p>See you soon!</p>
                          """
        })
        sms_text = communication.send_by_sms()[0]
        logger.info("SMS text result: \n" + sms_text)
        self.assertTrue(sms_text)
        self.assertNotIn('<p>', sms_text)
        self.assertNotIn('testing is fun', sms_text)
        self.assertNotIn('<br/>', sms_text)
        self.assertNotIn('<h1>', sms_text)
        self.assertNotIn('<a href', sms_text)
        self.assertNotIn('http://test', sms_text)
        self.assertIn('A communication example', sms_text)
        self.assertIn('\n\n', sms_text)
        tracked_link = self.env['link.tracker'].search([
            ('url', '=', 'http://test')
        ])
        self.assertTrue(tracked_link.short_url)
        self.assertIn(tracked_link.short_url, sms_text)
        self.assertTrue(sms_send_mock.called)
        self.assertEqual(communication.state, 'done')
        self.assertIsNotNone(communication.sms_cost)
