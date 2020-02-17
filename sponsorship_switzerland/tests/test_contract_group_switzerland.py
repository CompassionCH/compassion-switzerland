##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo.addons.sponsorship_compassion.tests \
    .test_sponsorship_compassion import BaseSponsorshipTest

from odoo.exceptions import UserError


class TestContractGroupSwitzerland(BaseSponsorshipTest):

    def setUp(self):
        super().setUp()
        self.michel.ref = 'reference'
        self.david.ref = 'refdavid'

    def test_compute_partner_bvr_ref(self):
        group = self.create_group({'partner_id': self.david.id})

        bvr_ref = group.compute_partner_bvr_ref()

        self.assertTrue(len(bvr_ref), 26)
        self.assertEqual(bvr_ref, u'00000000refdavid00001000007')

    def test_raise_error_if_the_bvr_becomes_invalid(self):
        group = self.create_group({'partner_id': self.michel.id})

        group.bvr_reference = 'invalid'
        with self.assertRaises(UserError) as e:
            group.on_change_bvr_ref()
        self.assertTrue('wrong format' in e.exception.name)

    def test_that_changing_payment_mode__regenerate_the_bvr_reference(self):
        group = self.create_group({'partner_id': self.michel.id})
        group.payment_mode_id = self.env['account.payment.mode'].browse(16)

        self.assertFalse(group.bvr_reference)
        group.on_change_payment_mode()
        self.assertEqual(len(group.bvr_reference), 27)
