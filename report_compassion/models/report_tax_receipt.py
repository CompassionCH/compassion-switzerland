##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from datetime import date

from odoo import api, models


class ReportTaxReceipt(models.AbstractModel):
    """
    Model used to generate tax receipt
    """

    _name = "report.report_compassion.tax_receipt"
    _description = "Used to generate tax receipt"

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data:
            data = {
                "year": date.today().year,
                "lang": self.env.context.get("lang", "en_US"),
            }
        if not docids and data["doc_ids"]:
            docids = data["doc_ids"]
        # We must retrieve the text of the receipt from the mail_template
        template = self.env.ref("report_compassion.tax_receipt_template").with_context(
            year=data["year"], lang=data["lang"]
        )
        texts = template._render_template(template.body_html, "res.partner", docids)
        lang = data.get("lang", self.env.lang)
        report = self.env["ir.actions.report"]._get_report_from_name(
            "report_compassion.tax_receipt"
        )
        data.update(
            {
                "doc_model": report.model,
                "docs": self.env[report.model].with_context(lang=lang).browse(docids),
                "texts": texts,
                "subject": template.subject,
                "docids": docids,
            }
        )

        return data
