
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
from odoo.tests.common import TransactionCase

logger = logging.getLogger(__name__)
geo_patch = 'odoo.addons.base_geolocalize.models.res_partner.geo_find'


class TestMessages(TransactionCase):
    def setUp(self):
        super().setUp()

        # Patch copied from test_partner_assign.py
        def geo_find(addr, apikey=False):
            return {
                'Wavre, Belgium': (50.7158956, 4.6128075),
                'Cannon Hill Park, B46 3AG Birmingham, United Kingdom':
                (52.45216, -1.898578),
            }.get(addr)
        patcher = patch(geo_patch, wraps=geo_find)
        patcher.start()

        res_partner = self.env['res.partner']
        church_vals = {
            'preferred_name': 'ChurchTest',
            'street': 'ChurchStreet 1',
            'zip': '2000',
            'firstname': 'Church',
            'name': 'Churchy Church',
            'city': 'ChurchCity',
            'lastname': 'Test',
            'ref': 'church_ref',
            'is_church': True,
            'lang': 'en_US',
            'phone': '+41 78 000 00 00'
        }
        self.church = res_partner.create(church_vals)
        # self.church.is_church = True

        custom_vals = {
            'preferred_name': 'TestPerson',
            'street': 'TestAddress 1',
            'zip': '2000',
            'firstname': 'Test',
            'name': 'Test Test',
            'city': 'TestCity',
            'lastname': 'Test',
            'ref': 'Test',
            'church_id': self.church.id,
            'lang': 'en_US',
            'phone': '+41 78 813 12 36'
        }
        # self.partner = res_partner.browse(18)
        self.partner = res_partner.create(custom_vals)
        self.addCleanup(patcher.stop)

    def test_name_search(self):
        res = self.env['res.partner'].search([('name', '=', 'Test Test')]).ids
        self.assertIn(self.partner.id, res)

    def test_get_lang_from_phone_number(self):
        lang = self.env['res.partner'].search([
            ('phone', '=', '+41 78 813 12 36')
        ]).mapped('lang')[0]
        self.assertEqual(lang, 'en_US')

    def test_update_sponsorship_number(self):s
        # fake sponsorship number (real is 0)
        self.partner.number_sponsorships = 5
        self.assertEqual(self.partner.number_sponsorships, 5)

        self.partner.update_number_sponsorships()
        self.assertEqual(self.partner.number_sponsorships, 0)

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
