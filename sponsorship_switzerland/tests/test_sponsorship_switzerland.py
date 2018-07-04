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


class TestSponsorshipSwitzerland(TransactionCase):

    def setUp(self):
        super(TestSponsorshipSwitzerland, self).setUp()

    def test_matching_using_partner_reference__when_no_client_is_matched(self):
        st_line = {'ref': 'xxxxxxxxx1111111'}

        rule = TestSponsorshipSwitzerland.fetch_rule_based_on_partner_ref(self)
        completion_result = rule.auto_complete([], st_line)

        self.assertEqual(completion_result, {})

    def test_matching_using_partner_reference__for_gifts(self):
        partner = '1512077'
        contract_not_in_db = '11111'
        gift = '4'
        st_line = {'ref': 'xxxxxxxxx' + partner + contract_not_in_db + gift}
        self.env['res.partner'].create({
            'name': 'Parter',
            'ref': '1512077'
        })

        rule = TestSponsorshipSwitzerland.fetch_rule_based_on_partner_ref(self)
        completion_result = rule.auto_complete([], st_line)

        self.assertTrue('partner_id' in completion_result)
        self.assertTrue('name' in completion_result)
        self.assertRegexpMatches(completion_result['name'], 'Project Gift.*')

    def fetch_rule_based_on_partner_ref(self):
        completion_rule_obj = self.env['account.statement.completion.rule']
        return completion_rule_obj.search(
            [('function_to_call', '=', 'get_from_partner_ref')]
        )
