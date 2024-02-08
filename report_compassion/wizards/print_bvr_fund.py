##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64

from odoo import api, fields, models


class PrintBvrFund(models.TransientModel):
    """
    Wizard for selecting a product and print
    payment slip of a partner.
    """

    _name = "print.bvr.fund"
    _description = "Select a product and print payment slip of a partner"

    product_id = fields.Many2one(
        "product.product",
        domain=[
            ("fund_id", "!=", False),
            ("fund_id", "!=", 0),
            # exclude Sponsorship category
            ("categ_id", "!=", 3),
            # exclude Sponsor gifts category
            ("categ_id", "!=", 5),
        ],
        readonly=False,
    )
    amount = fields.Float()
    state = fields.Selection([("new", "new"), ("pdf", "pdf")], default="new")
    pdf = fields.Boolean()
    pdf_name = fields.Char(default="fund.pdf")
    pdf_download = fields.Binary(readonly=True)

    def get_report(self):
        """
        Prepare data for the report and call the selected report
        (single bvr / 3 bvr).
        :return: Generated report
        """
        partners = self.env["res.partner"].browse(self.env.context.get("active_ids"))
        data = {
            "doc_ids": partners.ids,
            "product_id": self.product_id.id,
            "amount": self.amount or False,
            "communication": False,
        }
        report_ref = self.env.ref("report_compassion.report_bvr_fund")
        if self.pdf:
            self.pdf_name = self.product_id.name + ".pdf"
            pdf_data = report_ref.with_context(
                must_skip_send_to_printer=True
            )._render_qweb_pdf(partners.ids, data=data)[0]
            self.pdf_download = base64.encodebytes(pdf_data)
            self.state = "pdf"
            return {
                "name": "Download report",
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
                "context": self.env.context,
            }
        return report_ref.report_action(partners.ids, data=data, config=False)
