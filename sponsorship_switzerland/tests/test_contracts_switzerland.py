# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.addons.sponsorship_compassion.tests \
    .test_sponsorship_compassion import BaseSponsorshipTest

class TestContractsSwitzerland(BaseSponsorshipTest):

    def setUp(self):
        super(TestContractsSwitzerland, self).setUp()

    def test_compute_partner_bvr_ref(self):
        child = self.create_child('IO06790211')
        partner_id = self.michel.id
        group = self.create_group({'partner_id': partner_id})
        sponsorship = self.create_contract(
            {
                'type': 'SC',
                'child_id': child.id,
                'group_id': group.id,
                'partner_id': partner_id,
            },
            [{'amount': 50.0}]
        )

        sponsorship.on_change_group_id()

        #todo mock the date
        self.assertEqual(sponsorship.next_invoice_date, '2018-07-01')
