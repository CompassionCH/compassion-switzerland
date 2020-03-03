##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging

from odoo import api, models

logger = logging.getLogger(__name__)


class BvrSponsorshipGift(models.AbstractModel):
    """
    Model used for preparing data for the bvr report. It can either
    generate 3bvr report, 2bvr report or single bvr report.
    """
    _name = 'report.report_compassion.bvr_gift_sponsorship'
    _description = "Used for preparing data for a 3BVR or single BVR report (gifts)"

    def _get_report(self):
        return self.env['ir.actions.report']._get_report_from_name(
            'report_compassion.bvr_gift_sponsorship')

    def _get_default_data(self):
        """
        If no data is given for the report, use default values.
        :return: default mandatory data for the bvr report.
        """
        return {
            'product_ids': self.env[
                'recurring.contract'].get_sponsorship_gift_products().ids,
            'preprinted': False,
        }

    @api.model
    def get_report_values(self, docids, data=None):
        report = self._get_report()
        final_data = self._get_default_data()
        if data:
            final_data.update(data)
            if not docids and data['doc_ids']:
                docids = data['doc_ids']

        final_data.update({
            'doc_model': report.model,  # recurring.contract
            'docs': self.env[report.model].browse(docids),
            'doc_ids': docids,
            'products': self.env['product.product'].browse(
                final_data['product_ids'])
        })
        return final_data


# pylint: disable=consider-merging-classes-inherited
class TwoBvrGiftSponsorship(models.AbstractModel):
    _inherit = 'report.report_compassion.bvr_gift_sponsorship'
    _name = 'report.report_compassion.2bvr_gift_sponsorship'

    def _get_report(self):
        return self.env['report']._get_report_from_name(
            'report_compassion.2bvr_gift_sponsorship')


# pylint: disable=consider-merging-classes-inherited
class ThreeBvrGiftSponsorship(models.AbstractModel):
    _inherit = 'report.report_compassion.bvr_gift_sponsorship'
    _name = 'report.report_compassion.3bvr_gift_sponsorship'

    def _get_report(self):
        return self.env['ir.actions.report']._get_report_from_name(
            'report_compassion.3bvr_gift_sponsorship')

    @api.model
    def get_report_values(self, docids, data=None):
        if data is None:
            data = dict()
        data['offset'] = 1
        return super().get_report_values(
            docids, data)
