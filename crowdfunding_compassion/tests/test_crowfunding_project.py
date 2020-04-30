from odoo.tests.common import TransactionCase
from odoo import fields
from datetime import timedelta


class TestCrowdFunding(TransactionCase):

    def setUp(self):
        super().setUp()
        self.test_project = self.env['crowdfunding.project'].create({
            "name": "My super project",
            "type": "collective",
            "project_owner_id": "base.res_partner_address_15",
            "deadline": fields.Date.today() + timedelta(weeks=1),
        })

    def test_project_participants(self):
        """Test that participants are correctly updated after a change of owner"""
        self.assertEqual(len(self.test_project.participant_ids), 1)
        self.test_project.project_owner_id = self.env.ref("base.res_partner_address_16")
        self.assertCountEqual(len(self.test_project.participant_ids), 2)

    def test_project_ending(self):
        """Test that the project is archived at the end date"""
        end_time = fields.Date.today() + timedelta(weeks=1)
        self.assertEqual(self.test_project.deadline, end_time)
