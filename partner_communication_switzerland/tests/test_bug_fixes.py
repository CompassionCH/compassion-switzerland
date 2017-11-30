# -*- coding: utf-8 -*-
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
import mock
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion \
    import BaseSponsorshipTest


logger = logging.getLogger(__name__)

mock_update_hold = ('odoo.addons.child_compassion.models.compassion_hold'
                    '.CompassionHold.update_hold')


class TestSponsorship(BaseSponsorshipTest):

    def setUp(self):
        super(TestSponsorship, self).setUp()
        # Deactivate mandates of Michel Fletcher to avoid directly validate
        # sponsorship to waiting state.
        self.michel.ref = self.ref(7)
        self.mandates = self.env['account.banking.mandate'].search([
            ('partner_id', '=', self.michel.parent_id.id)])
        self.mandates.write({'state': 'draft'})

    @mock.patch(mock_update_hold)
    def test_co_1272(self, update_hold):
        """
            Test bug fix where mandate validation should not create a new
            dossier communication for the sponsor.
        """
        update_hold.return_value = True

        # Creation of the sponsorship contract
        child = self.create_child(self.ref(11))
        payment_mode_lsv = self.env.ref(
            'sponsorship_switzerland.payment_mode_lsv')
        sp_group = self.create_group({
            'partner_id': self.michel.id,
            'payment_mode_id': payment_mode_lsv.id,
        })
        sponsorship = self.create_contract(
            {
                'partner_id': self.michel.id,
                'group_id': sp_group.id,
                'child_id': child.id,
            },
            [{'amount': 50.0}]
        )
        # Check the sponsorship is in waiting mandate state
        self.validate_sponsorship(sponsorship)
        self.assertEqual(sponsorship.state, 'mandate')

        # Check the communication is generated after sponsorship validation
        new_dossier = self.env.ref(
            'partner_communication_switzerland.planned_dossier')
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.michel.id),
            ('state', '=', 'pending'),
            ('config_id', '=', new_dossier.id)
        ])
        self.assertTrue(partner_communications)

        # Remove the new dossier communication
        partner_communications.unlink()

        # Validate a mandate to make the sponsorship in waiting state.
        self.mandates[0].validate()
        self.assertEqual(sponsorship.state, 'waiting')

        # Check that no new communication is generated
        partner_communications = self.env['partner.communication.job'].search([
            ('partner_id', '=', self.michel.id),
            ('state', '=', 'pending'),
            ('config_id', '=', new_dossier.id)
        ])
        self.assertFalse(partner_communications)
