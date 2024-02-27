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

from odoo.addons.child_compassion.models.compassion_hold import HoldType
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)

mock_update_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.update_hold"
)


class TestHolds(BaseSponsorshipTest):
    def setUp(self):
        super().setUp()

        child1 = self.create_child(self.ref(11))
        sp_group = self.create_group({"partner_id": self.michel.id})
        self.sponsorship1 = self.create_contract(
            {
                "partner_id": self.michel.id,
                "group_id": sp_group.id,
                "child_id": child1.id,
            },
            [{"amount": 50.0}],
        )

        child2 = self.create_child(self.ref(11))
        sp_group2 = self.create_group({"partner_id": self.thomas.id})
        self.sponsorship2 = self.create_contract(
            {
                "partner_id": self.thomas.id,
                "group_id": sp_group2.id,
                "child_id": child2.id,
            },
            [{"amount": 50.0}],
        )

    @mock.patch(mock_update_hold)
    def test_hold_extension(self, update_hold):
        """sending reminder should not impact the no_money_extension field
        also hold should be extendable multiple times.
        """
        update_hold.return_value = True

        self.sponsorship1.hold_id.write(
            {
                "child_id": self.sponsorship1.child_id.id,
            }
        )

        self.sponsorship2.hold_id.write(
            {
                "type": HoldType.SUB_CHILD_HOLD.value,
                "child_id": self.sponsorship2.child_id.id,
            }
        )

        for sponsorship in [self.sponsorship1, self.sponsorship2]:
            self.assertEqual("draft", sponsorship.state)

            self.assertEqual(0, sponsorship.hold_id.no_money_extension)

            sponsorship.hold_id._send_hold_reminder(None)

            self.assertEqual(0, sponsorship.hold_id.no_money_extension)

            # assert hold can be extended multiple times
            for _ in range(4):
                previous_expiration = sponsorship.hold_id.expiration_date
                sponsorship.hold_id._send_hold_reminder(None)
                self.assertGreater(
                    sponsorship.hold_id.expiration_date, previous_expiration
                )
