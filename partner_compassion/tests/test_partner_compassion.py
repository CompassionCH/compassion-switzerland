
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
geo_patch = 'odoo.addons.base_geolocalize.models.base_geocoder.GeoCoder' \
    '.geo_find'


class TestMessages(TransactionCase):
    def setUp(self):
        super().setUp()

        # Patch copied from test_partner_assign.py
        def geo_find(addr):
            return {
                'Wavre, Belgium': (50.7158956, 4.6128075),
                'Cannon Hill Park, B46 3AG Birmingham, United Kingdom':
                (52.45216, -1.898578),
            }.get(addr)
        patcher = patch(geo_patch, wraps=geo_find)
        patcher.start()

        res_partner = self.env['res.partner']
        self.church = res_partner.browse(8)
        self.church.is_church = True

        custom_vals = {
            'preferred_name': 'Samuel',
            'street': 'Impasse des Fr\xeanes 1',
            'zip': '1669',
            'firstname': 'Samuel',
            'name': 'Fringeli Samuel',
            'city': 'Les Sciernes',
            'lastname': 'Fringeli',
            'ref': 'Fringeli',
            'church_id': self.church.id,
            'lang': 'en_US',
            'phone': '+41 78 813 12 36'
        }
        self.partner = res_partner.browse(18)
        self.partner.write(custom_vals)
        self.addCleanup(patcher.stop)

    def test_name_search(self):
        res = self.env['res.partner'].name_search('Fringeli')
        ids = [x[0] for x in res]
        self.assertIn(self.partner.id, ids)

    def test_get_lang_from_phone_number(self):
        phone = self.partner.phone.replace('\xa0', '')
        lang = self.env['res.partner'].get_lang_from_phone_number(phone)
        self.assertEqual(lang, 'en_US')

    def test_update_sponsorship_number(self):
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
