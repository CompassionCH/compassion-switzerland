# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging


from openerp import api, models, _
from openerp.exceptions import Warning

logger = logging.getLogger(__name__)


class BvrFundReport(models.Model):
    """
    Model used for preparing data for the bvr report.
    """
    _name = 'report.report_compassion.bvr_fund'

    @api.multi
    def render_html(self, data=None):
        """
        Construct the data for printing Payment Slips.
        :param data: data collected from the print wizard.
        :return: html rendered report
        """
        report = self.env['report']._get_report_from_name(
            'report_compassion.bvr_fund')
        if data is None:
            raise Warning(_("You must give a product in data to print this "
                            "report."))

        data.update({
            'doc_model': report.model,  # res.partner
            'docs': self.env[report.model].browse(data['doc_ids']),
            'product': self.env['product.product'].browse(data['product_id'])
        })
        return self.env['report'].render(report.report_name, data)
