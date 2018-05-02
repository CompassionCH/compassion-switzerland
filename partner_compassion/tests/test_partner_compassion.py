# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Samuel Fringeli <samuel.fringeli@me.com>
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.tests.common import TransactionCase
import logging

logger = logging.getLogger(__name__)


class TestMessages(TransactionCase):
    def setUp(self):
        super(TestMessages, self).setUp()

        res_partner = self.env['res.partner']
        self.church = res_partner.browse(8)
        self.church.is_church = True

        custom_vals = {
            u'preferred_name': u'Samuel',
            u'street': u'Impasse des Fr\xeanes 1',
            u'zip': u'1669',
            u'firstname': u'Samuel',
            u'name': u'Fringeli Samuel',
            u'city': u'Les Sciernes',
            u'lastname': u'Fringeli',
            u'ref': u'Fringeli',
            u'church_id': self.church.id,
            u'lang': u'en_US',
            u'phone': u'+41 78 813 12 36'
        }

        self.partner = res_partner.browse(18)
        self.partner.write(custom_vals)

    def test_name_search(self):
        res = self.env['res.partner'].name_search('Fringeli')
        ids = [x[0] for x in res]
        self.assertIn(self.partner.id, ids)

    def test_get_lang_from_phone_number(self):
        phone = self.partner.phone.replace(u'\xa0', u'')
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
