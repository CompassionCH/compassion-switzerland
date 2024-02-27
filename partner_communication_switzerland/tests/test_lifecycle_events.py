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

mock_process_commkit = (
    "odoo.addons.child_compassion.models.child_lifecycle_event"
    ".ChildLifecycleEvent.process_commkit"
)

mock_update_hold = (
    "odoo.addons.child_compassion.models.compassion_hold" ".CompassionHold.update_hold"
)

mock_get_info = (
    "odoo.addons.child_compassion.models.child_compassion" ".CompassionChild.get_infos"
)


class TestLifeCycle(BaseSponsorshipTest):
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

    @mock.patch(mock_get_info)
    @mock.patch(mock_update_hold)
    @mock.patch(mock_process_commkit)
    def test_communication_sent_on_planned_exit(
        self, mock_commkit, update_hold, get_info
    ):
        update_hold.return_value = True
        get_info.return_value = True

        # simulate a lifecylce planned exit entry for sponsorship1's child
        planned_exit_lif_cycle = self.env["compassion.child.ble"].create(
            {
                "child_id": self.sponsorship1.child_id.id,
                "global_id": self.ref(4),
                "type": "Registration",
            }
        )

        planned_exit_lif_cycle.update({"type": "Planned Exit"})

        mock_commkit.return_value = planned_exit_lif_cycle.ids

        self.sponsorship1.force_activation()

        self.sponsorship1.child_id.lifecycle_ids[:1].process_commkit(None)

        communication_type = self.env.ref(
            "partner_communication_switzerland.planned_exit_notification"
        )

        sent_comm = self.env["partner.communication.job"].search_count(
            [
                ("partner_id", "=", self.sponsorship1.partner_id.id),
                ("config_id", "=", communication_type.id),
            ]
        )

        self.assertTrue(sent_comm > 0)
