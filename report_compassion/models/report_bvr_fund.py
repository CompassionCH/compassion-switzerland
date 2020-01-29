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


from odoo import api, models, _
from odoo.exceptions import UserError

logger = logging.getLogger(__name__)


class BvrFundReport(models.AbstractModel):
    """
    Model used for preparing data for the bvr report.
    """
    _name = 'report.report_compassion.bvr_fund'
    _description = "Used for preparing data for the BVR report"

    @api.multi
    def render_html(self, docids, data=None):
        """
        Construct the data for printing Payment Slips.
        :param data: data collected from the print wizard.
        :return: html rendered report
        """
        report = self.env['report']._get_report_from_name(
            'report_compassion.bvr_fund')
        if data is None:
            # By default, prepare a report with background and try to read
            # product from context
            product_id = self.env.context.get('report_product_id')
            if not product_id:
                raise UserError(
                    _("You must give a product in data to print this "
                      "report."))
            data = {
                'background': True,
                'product_id': product_id,
                'preprinted': False,
                'amount': False,
                'communication': False
            }

        data.update({
            'doc_model': report.model,  # res.partner
            'docs': self.env[report.model].browse(docids),
            'product': self.env['product.product'].browse(data['product_id'])
        })
        return self.env['report'].render(report.report_name, data)
