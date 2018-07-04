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

        rule = self._fetch_rule_based_on_partner_ref()
        completion_result = rule.auto_complete([], st_line)

        self.assertEqual(completion_result, {})

    def test_matching_using_partner_reference__for_gifts(self):
        partner_ref = '1512077'
        contract_not_in_db = '11111'
        gift = '4'
        st_line = {
            'ref': 'xxxxxxxxx' + partner_ref + contract_not_in_db + gift
        }
        self._insert_partner_with_ref(partner_ref)

        rule = self._fetch_rule_based_on_partner_ref()
        completion_result = rule.auto_complete([], st_line)

        self.assertTrue('partner_id' in completion_result)
        self.assertTrue('name' in completion_result)
        self.assertRegexpMatches(completion_result['name'], 'Project Gift.*')

    def test_matching_by_bvr_reference__with_an_invoice_found(self):
        brv_ref = '1234'
        invoice104 = self.env['account.invoice'].browse([104])
        invoice104.write({'reference': brv_ref})

        rule = self._fetch_rule_by_function_name('get_from_bvr_ref')
        completion_result = rule.auto_complete([], {'ref': brv_ref})

        self.assertTrue('partner_id' in completion_result)
        self.assertEqual(completion_result['partner_id'], 8)
        self.assertEqual(invoice104.partner_id.commercial_partner_id.id, 8)

    def _fetch_rule_based_on_partner_ref(self):
        return self._fetch_rule_by_function_name('get_from_partner_ref')

    def _fetch_rule_by_function_name(self, rule_function_name):
        completion_rule_obj = self.env['account.statement.completion.rule']
        return completion_rule_obj.search(
            [('function_to_call', '=', rule_function_name)]
        )

    def _insert_partner_with_ref(self, ref):
        partner_obj = self.env['res.partner']
        partner_obj.create({
            'name': 'Partner',
            'ref': ref
        })
