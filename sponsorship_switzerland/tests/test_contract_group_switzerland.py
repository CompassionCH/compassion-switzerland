# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.tests.common import TransactionCase


class TestContractGroupSwitzerland(TransactionCase):

    def setUp(self):
        super(TestContractGroupSwitzerland, self).setUp()

    def test_contract_groups(self):
        brv_group = self.env['recurring.contract.group'] \
            .browse(['report_bvr_sponsorship'])

        self.assertEqual(len(brv_group), 1)
