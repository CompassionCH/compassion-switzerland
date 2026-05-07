##############################################################################
#
#    Copyright (C) 2016-2025 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import zipfile
from io import BytesIO

from odoo import _, fields, models
from odoo.exceptions import UserError


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
    state = fields.Selection([("new", "new"), ("download", "download")], default="new")
    output_type = fields.Selection(
        [("print", "Send to printer"), ("pdf", "PDF"), ("zip", "ZIP File")],
        default="print",
    )
    file_name = fields.Char(default="fund.pdf")
    file_download = fields.Binary(readonly=True)

    def get_report(self):
        self.ensure_one()
        partners = self.env["res.partner"].browse(
            self.env.context.get("active_ids", [])
        )
        if not partners:
            raise UserError(_("Please select at least one partner."))
        if not self.product_id:
            raise UserError(_("Please select a product to print the payment slip."))

        product_name = self.product_id.display_name or _("fund")
        report = self.env.ref("report_compassion.report_bvr_fund")
        base_data = {
            "doc_ids": partners.ids,
            "product_id": self.product_id.id,
            "amount": self.amount or False,
            "communication": False,
        }

        if self.output_type == "pdf":
            pdf_data = self._render_report_pdf(
                "report_compassion.report_bvr_fund", partners.ids, base_data
            )
            return self._prepare_download(f"{product_name}.pdf", pdf_data)

        if self.output_type == "zip":
            zip_data = self._build_zip_content(partners, base_data)
            return self._prepare_download(f"{product_name}.zip", zip_data)

        return report.report_action(partners.ids, data=base_data, config=False)

    def _render_report_pdf(self, report_ref, docids, data):
        return (
            self.env["ir.actions.report"]
            .with_context(must_skip_send_to_printer=True)
            ._render_qweb_pdf(report_ref, docids, data=data)[0]
        )

    def _build_zip_content(self, partners, base_data):
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, mode="w") as zip_file:
            for partner in partners:
                partner_data = dict(base_data, doc_ids=[partner.id])
                pdf_data = self._render_report_pdf(
                    "report_compassion.report_bvr_fund", partner.ids, partner_data
                )
                pdf_filename = f"{partner.ref or partner.id}.pdf"
                zip_file.writestr(pdf_filename, pdf_data)
        return buffer.getvalue()

    def _prepare_download(self, filename, content):
        self.write(
            {
                "file_name": filename,
                "file_download": base64.encodebytes(content),
                "state": "download",
            }
        )
        return self._download_action()

    def _download_action(self):
        return {
            "name": _("Download report"),
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
