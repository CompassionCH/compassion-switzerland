##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.tests.common import TransactionCase


class TestCompletionRulesSwitzerland(TransactionCase):

    def setUp(self):
        super().setUp()

    def test_matching_using_partner_reference__when_no_client_is_matched(self):
        st_line = {'ref': 'xxxxxxxxx1111111'}

        rule = self._fetch_rule_by_function_name('get_from_partner_ref')
        completion_result = rule.auto_complete([], st_line)

        self.assertEqual(completion_result, {})

    def test_matching_using_partner_reference_for_gifts(self):
        partner_ref = '1512077'
        contract_not_in_db = '11111'
        gift_type = '4'
        st_line = {
            'ref': 'x' * 9 + partner_ref + contract_not_in_db + gift_type +
            '0' * 5
        }
        self._insert_partner(ref=partner_ref)

        rule = self._fetch_rule_by_function_name('get_from_partner_ref')
        completion_result = rule.auto_complete([], st_line)

        self.assertTrue('partner_id' in completion_result)
        self.assertTrue('name' in completion_result)
        self.assertRegexpMatches(completion_result['name'], 'Project Gift.*')

    def test_lookup_by_sponsor_name(self):
        statement_line = {'name': u' EXPÉDITEUR: fost edward'}

        rule = self._fetch_rule_by_function_name('get_sponsor_name')
        completion_result = rule.auto_complete([], statement_line)

        self.assertTrue('partner_id' in completion_result)
        self.assertEqual(completion_result['partner_id'], 8)

    def test_lookup_by_sponsor_name_with_multiple_matching(self):
        """
        Two partners match flexible search by name (User Demo and User
        Portal Demo) and the exact match should take precedence
        """
        statement_line = {'name': u' EXPÉDITEUR: user demo'}

        rule = self._fetch_rule_by_function_name('get_sponsor_name')
        completion_result = rule.auto_complete([], statement_line)

        self.assertTrue('partner_id' in completion_result)
        self.assertEqual(completion_result['partner_id'], 6)

    def test_lookup_by_sponsor_name_for_companies(self):
        """
        Looking up corporate partner 'Agrolait'
        Edge case of having a single word instead of first + last name
        """
        statement_line = {'name': u' DONNEUR D\'ORDRE: Grolai'}

        rule = self._fetch_rule_by_function_name('get_sponsor_name')
        completion_result = rule.auto_complete([], statement_line)

        self.assertTrue('partner_id' in completion_result)
        self.assertEqual(completion_result['partner_id'], 8)

    def test_lookup_by_sponsor_name_with_wire_transfers(self):
        """
        The logic to split the names is slightly different
        """
        statement_line = {'name': u'VIREMENT DU COMPTE CH01 edward fost'}

        rule = self._fetch_rule_by_function_name('get_sponsor_name')
        completion_result = rule.auto_complete([], statement_line)

        self.assertTrue('partner_id' in completion_result)
        self.assertEqual(completion_result['partner_id'], 8)

    def test_lsv_dd_for_postfinance(self):
        statement_line = {
            'name': u'anything\nKREDITKARTEN\nanything',
            'amount': 200
        }

        rule = self._fetch_rule_by_function_name('get_from_lsv_dd')
        completion_result = rule.auto_complete([], statement_line)

        self.assertTrue('account_id' in completion_result)
        self.assertEqual(completion_result['account_id'], 69)
        self.assertTrue('partner_id' in completion_result)

    def test_lsv_dd(self):
        statement_line = {
            'name': u'anything\n CRÉDIT GROUPÉ BVR\nanything',
            'amount': 200
        }

        rule = self._fetch_rule_by_function_name('get_from_lsv_dd')
        completion_result = rule.auto_complete([], statement_line)

        self.assertFalse('partner_id' in completion_result)
        self.assertTrue('account_id' in completion_result)

    def test_lsv_dd_with_zero_amount(self):
        rule = self._fetch_rule_by_function_name('get_from_lsv_dd')
        completion_result = rule.auto_complete([], {'amount': 0, 'name': ''})

        self.assertEqual(completion_result, {})

    def _fetch_rule_by_function_name(self, rule_function_name):
        completion_rule_obj = self.env['account.statement.completion.rule']
        return completion_rule_obj.search(
            [('function_to_call', '=', rule_function_name)]
        )

    def _insert_partner(self, ref):
        partner_obj = self.env['res.partner']
        partner_obj.create({
            'name': 'Partner',
            'ref': ref
        })
