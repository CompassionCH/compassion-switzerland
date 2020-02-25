##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo.addons.sponsorship_compassion.tests.test_sponsorship_compassion \
    import BaseSponsorshipTest


class TestMobileAppConnector(BaseSponsorshipTest):

    def test_get_sms_sponsor_child_data(self):
        child = self.create_child('AA4239181')
        child.desc_fr = 'fr description'

        result = child.with_context(lang='fr_CH') \
            .get_sms_sponsor_child_data()

        self.assertEqual(result['description'], 'fr description')
