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
