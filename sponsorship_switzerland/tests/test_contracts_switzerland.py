##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import datetime

import mock

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)

time_path = "odoo.addons.sponsorship_switzerland.models.contracts.datetime"


class TestContractsSwitzerland(BaseSponsorshipTest):
    def setUp(self):
        super().setUp()

    @mock.patch(time_path)
    def test_on_change_group_id__recomputes_next_invoice_date(self, time_mock):
        sponsorship = self._create_sponsorship()
        fake_date = datetime.date(2015, 2, 5)
        time_mock.date.today.return_value = fake_date

        sponsorship.on_change_group_id()

        self.assertEqual(sponsorship.next_invoice_date, fake_date.replace(day=1))

    def test_sponsorship_termination(self):
        sponsorship = self._create_sponsorship(contract_type="S")

        sponsorship.contract_terminated()

    def _create_sponsorship(self, contract_type="SC"):
        child = self.create_child("IO06790211")
        partner_id = self.michel.id
        group = self.create_group({"partner_id": partner_id})
        return self.create_contract(
            {
                "type": contract_type,
                "child_id": child.id,
                "group_id": group.id,
                "partner_id": partner_id,
                "activation_date": datetime.datetime.today(),
            },
            [{"amount": 50.0}],
        )
