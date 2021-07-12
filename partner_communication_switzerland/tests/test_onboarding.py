##############################################################################
#
#    Copyright (C) 2021 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Jonathan Guerne <guernej@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import mock
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)

mock_update_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.update_hold"
)


class TestOnBoarding(BaseSponsorshipTest):


    def setUp(self):
        super().setUp()
        self.michel.ref = self.ref(7)

        payment_mode_lsv = self.env.ref("sponsorship_switzerland.payment_mode_lsv")
        self.sp_group = self.create_group(
            {"partner_id": self.michel.id, "payment_mode_id": payment_mode_lsv.id, }
        )

    @mock.patch(mock_update_hold)
    def test_correct_onboarding_start_date(self, hold_mock):
        """onboarding_start_date should be set once the welcome communication is sent"""

        hold_mock.return_value = True

        child = self.create_child(self.ref(11))
        partner = self.michel

        sponsorship = self.create_contract(
            {
                "partner_id": partner.id,
                "group_id": self.sp_group.id,
                "child_id": child.id,
            },
            [{"amount": 50.0}],
        )

        sponsorship.contract_waiting()

        welcome_ref = self.env.ref("partner_communication_switzerland.config_onboarding_sponsorship_confirmation")

        welcome_job = self.env["partner.communication.job"].search([
            ("config_id", "=", welcome_ref.id),
            ("partner_id", "=", sponsorship.correspondent_id.id)
        ])

        self.assertIsNot(welcome_job, False)
        self.assertFalse(sponsorship.onboarding_start_date)

        welcome_job.send()

        self.assertIsNot(sponsorship.onboarding_start_date, False)
