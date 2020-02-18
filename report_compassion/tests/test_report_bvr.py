##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Nicolas Bornand
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from odoo.addons.sponsorship_switzerland.tests \
    .test_contracts_switzerland import TestContractsSwitzerland

_logger = logging.getLogger(__name__)


class TestReportBVRSponsorship(TestContractsSwitzerland):

    def setUp(self):
        super().setUp()
        self.product = self.env.ref('product.service_order_01')

    def test_report_bvr_sponsorship__render_html(self):
        sponsorship = self._create_sponsorship()

        report = self.env['report.report_compassion.bvr_sponsorship']
        html_dict = report.get_report_values([sponsorship.id])

        self.assertIsInstance(html_dict, dict,
                              "There was an error while compiling the report.")
