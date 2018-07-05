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
import datetime


class TestContractsSwitzerland(BaseSponsorshipTest):

    def setUp(self):
        super(TestContractsSwitzerland, self).setUp()
        self._mock_date_5_feb_2015()

    def test_on_change_group_id__recomputes_next_invoice_date(self):
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

        self.assertEqual(sponsorship.next_invoice_date, '2018-07-01')
