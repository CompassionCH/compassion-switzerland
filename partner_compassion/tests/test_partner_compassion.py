##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samuel Fringeli <samuel.fringeli@me.com>
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from mock import patch

from odoo.tests import tagged

from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion import (
    BaseSponsorshipTest,
)

mock_update_hold = (
    "odoo.addons.child_compassion.models.compassion_hold.CompassionHold.update_hold"
)

logger = logging.getLogger(__name__)
geo_patch = "odoo.addons.base_geolocalize.models.res_partner.geo_find"


@tagged("wip_test")
class TestMessages(BaseSponsorshipTest):
    def setUp(self):
        super().setUp()

        # Patch copied from test_partner_assign.py
        def geo_find(addr, apikey=False):
            return {
                "Wavre, Belgium": (50.7158956, 4.6128075),
                "Cannon Hill Park, B46 3AG Birmingham, United Kingdom": (
                    52.45216,
                    -1.898578,
                ),
            }.get(addr)

        patcher = patch(geo_patch, wraps=geo_find)
        patcher.start()

        self.origin_id = (
            self.env["recurring.contract.origin"].create({"type": "event"}).id
        )

        res_partner = self.env["res.partner"]
        church_vals = {
            "preferred_name": "ChurchTest",
            "street": "ChurchStreet 1",
            "zip": "2000",
            "firstname": "Church",
            "name": "Churchy Church",
            "city": "ChurchCity",
            "lastname": "Test",
            "ref": "church_ref",
            "is_church": True,
            "lang": "en_US",
            "phone": "+41 78 000 00 00",
        }
        self.church = res_partner.create(church_vals)

        custom_vals = {
            "preferred_name": "TestPerson",
            "street": "TestAddress 1",
            "zip": "2000",
            "firstname": "Test",
            "name": "Test Test",
            "city": "TestCity",
            "lastname": "Test",
            "ref": "Test",
            "church_id": self.church.id,
            "lang": "en_US",
            "phone": "+41 78 813 12 36",
        }
        self.partner = res_partner.create(custom_vals)
        self.addCleanup(patcher.stop)

    def test_name_search(self):
        res = self.env["res.partner"].search([("name", "=", "Test Test")]).ids
        self.assertIn(self.partner.id, res)

    def test_get_lang_from_phone_number(self):
        lang = (
            self.env["res.partner"]
            .search([("phone", "=", "+41 78 813 12 36")])
            .mapped("lang")[0]
        )
        self.assertEqual(lang, "en_US")

    def test_update_sponsorship_number(self):
        # fake sponsorship number (real is 0)
        self.partner.number_sponsorships = 5
        self.assertEqual(self.partner.number_sponsorships, 5)

        self.partner.update_number_sponsorships()
        self.assertEqual(self.partner.number_sponsorships, 0)

        sp_group = self.create_group(
            {
                "change_method": "do_nothing",
                "partner_id": self.michel.id,
                "advance_billing_months": 1,
                "payment_mode_id": self.payment_mode.id,
            }
        )

        for i, child_ref in enumerate(["UG72320010", "S008320011", "SA12311013"]):
            child = self.create_child(child_ref)
            sp = self.create_contract(
                {
                    "partner_id": self.partner.id,
                    "child_id": child.id,
                    "group_id": sp_group.id,
                },
                [{"amount": 42}],
            )
            self.validate_sponsorship(sp)
            sp.contract_active()

            self.assertEqual(self.partner.number_sponsorships, i + 1)
            self.assertEqual(self.church.number_sponsorships, i + 1)

    # things with duplicated partners and onchange method don't work
    # def test_duplicate(self):
    #     # test if duplicated is in self.partner
    #    duplicated = self.duplicated_partner.partner_duplicate_ids\
    #        .mapped('id')
    #    self.assertIn(self.partner.id, duplicated)
    #
    #    # test if self.partner is in duplicated
    #    duplicated = self.partner.partner_duplicate_ids.mapped('id')
    #    self.assertIn(self.duplicated_partner.id, duplicated)
    #
    # def test_onchange_partner(self):
    #     partner = self.env['res.partner'].browse(self.partner.id)
    #     partner._origin = partner
    #     res = partner.onchange_partner()
    #     # shoud be a duplicate that produces a warning message
    #     self.assertIn('warning', res)
