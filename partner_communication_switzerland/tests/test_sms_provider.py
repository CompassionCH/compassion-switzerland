##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon <gigon.quentin@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import mock

from odoo.tests import HttpCase


class TestSmsProvider(HttpCase):
    _name = "my.classs"

    def setUp(self):
        super().setUp()
        self.partner = self.env.ref('base.res_partner_1')

    @mock.patch('odoo.addons.sms_939.models.sms_api.SmsApi._smsbox_send')
    def test_sms_provider(self, smsbox_send):
        wizard = self.env['partner.communication.generate.wizard'].create({
            'name': 'test',
            'force_language': 'fr_CH',
            'sms_provider_id': self.env.ref('sms_939.small_account_id').id,
            'send_mode': 'sms',
            'partner_ids': [(6, 0, self.partner.ids)],
        })

        result = wizard.generate()

        communication_job = self.env['partner.communication.job'].search([
            ('id', '=', result['domain'][0][2][0])
        ])

        self.assertEqual(self.env.ref('sms_939.small_account_id').id,
                         communication_job.sms_provider_id.id)
