##############################################################################
#
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
from datetime import date

from odoo import _, api, fields, models
from odoo.tools.pdf import merge_pdf


class PrintTaxReceipt(models.TransientModel):
    """
    Wizard for selecting a the child dossier type and language.
    """

    _name = "print.tax_receipt"
    _description = "Select a tax receipt"

    state = fields.Selection([("new", "new"), ("pdf", "pdf")], default="new")
    year = fields.Integer(default=date.today().year - 1)
    pdf = fields.Boolean()
    pdf_name = fields.Char(default="tax_receipt.pdf")
    pdf_download = fields.Binary(readonly=True)

    @api.onchange("year")
    def onchange_year(self):
        this_year = date.today().year
        if self.year >= this_year:
            return {
                "warning": {
                    "title": _("Year is incomplete"),
                    "message": _(
                        "Payments for the selected year are not yet "
                        "registered completely. The tax receipt may "
                        "be incomplete."
                    ),
                }
            }

    def get_report(self):
        """
        Call when button 'Get Report' clicked.
        Print tax receipt
        :return: Generated report
        """
        model = "res.partner"
        records = self.env[model].browse(self.env.context.get("active_ids"))
        # Each receipt is in the language of its donor, also when someone
        # prints it for them from the backend. MyCompassion asks for the
        # language of the website session instead (tax_receipt_lang).
        session_lang = self.env.context.get("tax_receipt_lang")
        partners_by_lang = (
            {session_lang: records}
            if session_lang
            else records.grouped(lambda p: p.lang or self.env.lang)
        )
        if not self.pdf and len(partners_by_lang) == 1:
            lang, partners = next(iter(partners_by_lang.items()))
            return (
                self.env.ref("report_compassion.tax_receipt_report")
                .with_context(lang=lang)
                .report_action(
                    partners.ids, data=self._get_data(partners, lang), config=False
                )
            )

        # A PDF to download: asked for, or several languages, which can't go
        # in one printing
        pdf_data = merge_pdf(
            [
                self.env["ir.actions.report"]
                .with_context(lang=lang, must_skip_send_to_printer=True)
                .sudo()
                ._render_qweb_pdf(
                    "report_compassion.tax_receipt_report",
                    partners.ids,
                    data=self._get_data(partners, lang),
                )[0]
                for lang, partners in partners_by_lang.items()
            ]
        )
        name_lang = session_lang or (
            next(iter(partners_by_lang))
            if len(partners_by_lang) == 1
            else self.env.lang
        )
        self.pdf_download = base64.encodebytes(pdf_data)
        self.pdf_name = (
            self.with_context(lang=name_lang).env._("tax_receipt") + f"_{self.year}.pdf"
        )
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

    def _get_data(self, partners, lang):
        return {"doc_ids": partners.ids, "year": self.year, "lang": lang}
