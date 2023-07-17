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

    _name = "report.report_compassion.bvr_fund"
    _description = "Used for preparing data for the BVR report"

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env["ir.actions.report"]._get_report_from_name(
            "report_compassion.bvr_fund"
        )
        if data is None:
            data = {
                "amount": False,
                "communication": False,
            }
        if "product_id" not in data:
            # try to read product from context
            product_id = self.env.context.get("report_product_id")
            if not product_id:
                raise UserError(
                    _("You must give a product in data to print this report.")
                )
            data["product_id"] = product_id

        if not docids and data["doc_ids"]:
            docids = data["doc_ids"]

        data.update(
            {
                "doc_model": report.model,  # res.partner
                "docs": self.env[report.model].browse(docids),
                "product": self.env["product.product"].browse(data["product_id"]),
            }
        )
        return data
