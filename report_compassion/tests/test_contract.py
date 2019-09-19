# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo.addons.sponsorship_switzerland.tests \
    .test_contracts_switzerland import TestContractsSwitzerland

_logger = logging.getLogger(__name__)


class TestContract(TestContractsSwitzerland):

    def setUp(self):
        super(TestContract, self).setUp()
        self.product = self.env.ref('product.service_order_01')

    def test_get_gift_communication(self):
        sponsorship = self._create_sponsorship()

        communication = sponsorship.get_gift_communication(self.product)

        expected = u'Test (IO06790211)<br/>Prepaid Consulting<br/>'
        self.assertEqual(communication, expected)

    def test_group__get_months__for_frequency_one(self):
        sponsorship = self._create_sponsorship()
        group = self.create_group({'partner_id': self.michel.id})

        months_in_future = ['2050-08-01', '2050-09-01']
        months = group.get_months(months_in_future, sponsorship)

        self.assertEqual(len(months), 2)

    def test_group__get_months__with_advance(self):
        sponsorship = self._create_sponsorship()
        group = self.create_group({'partner_id': self.michel.id})
        group.advance_billing_months = 5

        months_in_future = ['2050-08-01', '2050-09-01']
        months = group.get_months(months_in_future, sponsorship)

        self.assertListEqual(months, ['2050-08-01 - 2050-09-01'])

    def test_group__get_communication__for_permanent_order(self):
        sponsorship = self._create_sponsorship()
        group = sponsorship.group_id
        group.advance_billing_months = 5
        group.payment_mode_id = self.env \
            .ref('sponsorship_switzerland.payment_mode_permanent_order')

        date = '2050-08-01'
        payment_slip = group.get_communication(date, date, sponsorship)

        expected = u'ISR for standing order CHF 50<br/>Test (IO06790211)<br/>'
        self.assertEqual(payment_slip, expected)
