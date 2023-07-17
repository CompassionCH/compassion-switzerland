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

from odoo import api, models, fields


class PrintChildpack(models.TransientModel):
    """
    Wizard for selecting a the child dossier type and language.
    """

    _name = "print.childpack"
    _description = "Select the child dossier type and language"

    type = fields.Selection(
        [
            ("report_compassion.childpack_full", "Full Childpack"),
            ("report_compassion.childpack_small", "Small Childpack"),
            ("report_compassion.childpack_mini", "Mini Childpack"),
        ],
        default=lambda s: s._default_type(),
    )
    lang = fields.Selection("_lang_selection", default=lambda s: s._default_lang())
    state = fields.Selection([("new", "new"), ("pdf", "pdf")], default="new")
    pdf = fields.Boolean()
    pdf_name = fields.Char(default="fund.pdf")
    pdf_download = fields.Binary(readonly=True)

    @api.model
    def _lang_selection(self):
        languages = self.env["res.lang"].search([])
        return [(language.code, language.name) for language in languages]

    @api.model
    def _default_type(self):
        child = self.env["compassion.child"].browse(self.env.context.get("active_id"))
        if child.sponsor_id:
            return "report_compassion.childpack_small"
        return "report_compassion.childpack_full"

    @api.model
    def _default_lang(self):
        child = self.env["compassion.child"].browse(self.env.context.get("active_id"))
        if child.sponsor_id:
            return child.sponsor_id.lang
        return self.env.lang

    def get_report(self):
        """
        Print selected child dossier
        :return: Generated report
        """
        children = (
            self.env["compassion.child"]
            .browse(self.env.context.get("active_ids"))
            .with_context(lang=self.lang)
        )
        data = {
            "lang": self.lang,
            "doc_ids": children.ids,
            "is_pdf": self.pdf,
            "type": self.type,
        }
        report_name = "report_compassion.report_" + self.type.split(".")[1]
        report_ref = self.env.ref(report_name).with_context(lang=self.lang)
        if self.pdf:
            name = children.local_id if len(children) == 1 else "dossiers"
            self.pdf_name = f"{name}_{self.type.split('.')[1].split('_')[1]}_{self.lang.split('_')[0]}.pdf"
            pdf_data = report_ref.with_context(
                must_skip_send_to_printer=True
            )._render_qweb_pdf(children.ids, data=data)
            self.pdf_download = base64.encodebytes(pdf_data[0])
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
        return report_ref.report_action(children.ids, data=data, config=False)

    def print(self):
        """
        Print selected child dossier directly to printer
        """
        children = (
            self.env["compassion.child"]
            .browse(self.env.context.get("active_ids"))
            .with_context(lang=self.lang)
        )
        data = {
            "lang": self.lang,
            "doc_ids": children.ids,
            "is_pdf": self.pdf,
            "type": self.type,
        }
        report_name = "report_compassion.report_" + self.type.split(".")[1]
        report_ref = self.env.ref(report_name).with_context(lang=self.lang)
        report_ref._render_qweb_pdf(children.ids, data=data)
        return True
