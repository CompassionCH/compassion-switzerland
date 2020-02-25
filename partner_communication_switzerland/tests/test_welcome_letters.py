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
from datetime import date

import mock
from dateutil.relativedelta import relativedelta
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion \
    import BaseSponsorshipTest

from odoo.tools import file_open
from odoo import fields


logger = logging.getLogger(__name__)

mock_update_hold = ('odoo.addons.child_compassion.models.compassion_hold'
                    '.CompassionHold.update_hold')
mock_get_pdf = 'odoo.addons.base_report_to_printer.models' \
               '.ir_actions_report.IrActionsReport.render_qweb_pdf'

mock_force_activation = 'odoo.addons.recurring_contract.models.' \
                        'recurring_contract.RecurringContract.force_activation'


class TestSponsorship(BaseSponsorshipTest):

    def setUp(self):
        super().setUp()
        # Deactivate mandates of Michel Fletcher to avoid directly validate
        # sponsorship to waiting state.
        self.thomas.ref = self.ref(7)
        self.michel.ref = self.ref(7)
        self.mandates = self.env['account.banking.mandate'].search([
            ('partner_id', '=', self.michel.parent_id.id)])
        self.mandates.write({'state': 'draft'})
        payment_mode_lsv = self.env.ref(
            'sponsorship_switzerland.payment_mode_lsv')
        self.lsv_group = self.create_group({
            'partner_id': self.michel.id,
            'payment_mode_id': payment_mode_lsv.id,
        })
        self.bvr_group = self.create_group({
            'partner_id': self.thomas.id,
            'payment_mode_id': self.env.ref(
                'sponsorship_switzerland.payment_mode_bvr').id,
        })

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_welcome_letters_normal(self, get_pdf, update_hold):
        """
        Create a sponsorship, validate it, activate it and test that
        welcome e-mail and welcome active communications are sent on the
        right time.

        Welcome e-mail should be sent 10 days after contract validation
        Welcome active should be sent after activation, at least 5 days after
        contract validation.
        """
        update_hold.return_value = True
        f_path = 'addons/partner_communication_switzerland/static/src/test.pdf'
        with file_open(f_path, 'rb') as pdf_file:
            get_pdf.return_value = pdf_file.read()

        # Creation of the sponsorship contract
        child = self.create_child(self.ref(11))
        sponsorship = self.create_contract(
            {
                'partner_id': self.thomas.id,
                'group_id': self.bvr_group.id,
                'child_id': child.id,
            },
            [{'amount': 50.0}]
        )
        self.validate_sponsorship(sponsorship)
        self.assertEqual(sponsorship.sds_state, 'waiting_welcome')
        # Perform action rules (shouldn't do anything)
        self.env['base.automation']._check()
        self.assertEqual(sponsorship.sds_state, 'waiting_welcome')

        # Simulate the SDS state was in 10 days and check the welcome e-mail
        # is sent.
        eleven_days_ago = date.today() - relativedelta(days=11)
        sponsorship.sds_state_date = fields.Date.to_string(eleven_days_ago)
        self.env.ref('partner_communication_switzerland.check_welcome_email') \
            .last_run = fields.Date.to_string(eleven_days_ago)
        sponsorship.send_welcome_letter()
        self.assertEqual(sponsorship.sds_state, 'active')

        # Check the communication is generated after sponsorship validation
        welcome_email = self.env.ref(
            'partner_communication_switzerland.planned_welcome')
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('state', '=', 'pending'),
            ('config_id', '=', welcome_email.id)
        ])
        self.assertTrue(partner_communications)

        # Now test the welcome active communication
        sponsorship.force_activation()
        two_days_ago = date.today() - relativedelta(days=2)
        sponsorship.activation_date = fields.Date.to_string(two_days_ago)
        sponsorship._send_welcome_active_letters_for_activated_sponsorships()
        welcome_active = self.env.ref(
            'partner_communication_switzerland.welcome_activation')
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('config_id', '=', welcome_active.id)
        ])
        self.assertFalse(partner_communications)
        self.assertFalse(sponsorship.welcome_active_letter_sent)

        # Now set the start date in the past and welcome active should be sent
        sponsorship.start_date = fields.Date.to_string(eleven_days_ago)
        sponsorship._send_welcome_active_letters_for_activated_sponsorships()
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('config_id', '=', welcome_active.id),
            ('state', '=', 'done')
        ])
        self.assertTrue(partner_communications)
        self.assertTrue(sponsorship.welcome_active_letter_sent)

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_no_welcome_letters(self, get_pdf, update_hold):
        """
        Create a sponsorship, mark welcome letters already sent and test
        they are not sent when contract is validated and activated.
        """
        update_hold.return_value = True
        f_path = 'addons/partner_communication_switzerland/static/src/test.pdf'
        with file_open(f_path, 'rb') as pdf_file:
            get_pdf.return_value = pdf_file.read()

        # Creation of the sponsorship contract
        child = self.create_child(self.ref(11))
        sponsorship = self.create_contract(
            {
                'partner_id': self.thomas.id,
                'group_id': self.bvr_group.id,
                'child_id': child.id,
                'welcome_active_letter_sent': True
            },
            [{'amount': 50.0}]
        )

        self.validate_sponsorship(sponsorship)
        self.assertEqual(sponsorship.sds_state, 'active')
        # Perform action rules (shouldn't do anything)
        eleven_days_ago = date.today() - relativedelta(days=11)
        sponsorship.sds_state_date = fields.Date.to_string(eleven_days_ago)
        self.env['base.automation']._check()
        self.assertEqual(sponsorship.sds_state, 'active')
        welcome_email = self.env.ref(
            'partner_communication_switzerland.planned_welcome')
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('config_id', '=', welcome_email.id)
        ])
        self.assertFalse(partner_communications)

        # Now test the welcome active communication
        sponsorship.force_activation()
        two_days_ago = date.today() - relativedelta(days=2)
        sponsorship.activation_date = fields.Date.to_string(two_days_ago)
        sponsorship.start_date = fields.Date.to_string(eleven_days_ago)
        sponsorship._send_welcome_active_letters_for_activated_sponsorships()
        welcome_active = self.env.ref(
            'partner_communication_switzerland.welcome_activation')
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.thomas.id),
            ('config_id', '=', welcome_active.id)
        ])
        self.assertFalse(partner_communications)

    @mock.patch(mock_update_hold)
    @mock.patch(mock_get_pdf)
    def test_no_welcome_letter_for_transfers(self, get_pdf, update_hold):
        child = self.create_child(self.ref(11))
        transfer_origin = self.env['recurring.contract.origin'].create({
            'type': 'transfer'
        })
        sponsorship = self.create_contract(
            {
                'partner_id': self.michel.id,
                'child_id': child.id,
                'group_id': self.lsv_group.id,
                'origin_id': transfer_origin.id

            },
            [{'amount': 50.0}]
        )
        partner_communications = self.env['partner.communication.job']
        count_before = partner_communications.search_count([])

        sponsorship.send_welcome_letter()

        self.assertEqual(sponsorship.sds_state, 'active')
        # No new communication is generated
        self.assertEqual(count_before, partner_communications.search_count([]))
