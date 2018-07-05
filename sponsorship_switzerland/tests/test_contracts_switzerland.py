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
import mock
import datetime

time_path = ('odoo.addons.sponsorship_switzerland.models.contracts'
             '.CurrentTime')


class TestContractsSwitzerland(BaseSponsorshipTest):

    def setUp(self):
        super(TestContractsSwitzerland, self).setUp()

    @mock.patch(time_path)
    def test_on_change_group_id__recomputes_next_invoice_date(self, time_mock):
        sponsorship = self._create_sponsorship()
        time_mock.now.return_value = datetime.date(2015, 2, 5)

        sponsorship.on_change_group_id()

        self.assertEqual(sponsorship.next_invoice_date, '2015-02-01')

    def test_sponsorship_termination(self):
        sponsorship = self._create_sponsorship(contract_type='S')

        self.assertEqual(self.michel.number_sponsorships, 0)
        sponsorship.contract_terminated()
        self.assertEqual(self.michel.number_sponsorships, 1)

    def _create_sponsorship(self, contract_type='SC'):
        child = self.create_child('IO06790211')
        partner_id = self.michel.id
        group = self.create_group({'partner_id': partner_id})
        return self.create_contract(
            {
                'type': contract_type,
                'child_id': child.id,
                'group_id': group.id,
                'partner_id': partner_id,
            },
            [{'amount': 50.0}]
        )
