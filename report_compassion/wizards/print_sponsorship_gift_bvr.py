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

from odoo.addons.sponsorship_compassion.models.product_names \
    import GIFT_PRODUCTS_REF

from odoo import models, fields, _
from odoo.exceptions import Warning as odooWarning


class PrintSponsorshipBvr(models.TransientModel):
    """
    Wizard for selecting a period and the format for printing
    payment slips of a sponsorship.
    """

    _name = "print.sponsorship.gift.bvr"
    _description = (
        "Select a period and the format for printing "
        "the payment slips of a sponsorship"
    )

    birthday_gift = fields.Boolean(default=True)
    general_gift = fields.Boolean(default=True)
    family_gift = fields.Boolean(default=True)
    project_gift = fields.Boolean()
    graduation_gift = fields.Boolean()

    paper_format = fields.Selection(
        [
            ("report_compassion.2bvr_gift_sponsorship", "2 BVR"),
            ("report_compassion.bvr_gift_sponsorship", "Single BVR"),
        ],
        default="report_compassion.2bvr_gift_sponsorship",
    )
    state = fields.Selection([("new", "new"), ("pdf", "pdf")], default="new")
    pdf = fields.Boolean()
    pdf_name = fields.Char(default="fund.pdf")
    pdf_download = fields.Binary(readonly=True)

    def get_report(self):
        """
        Prepare data for the report and call the selected report
        (single bvr / 2 bvr).
        :return: Generated report
        """
        product_search = list()
        if self.birthday_gift:
            product_search.append(GIFT_PRODUCTS_REF[0])
        if self.general_gift:
            product_search.append(GIFT_PRODUCTS_REF[1])
        if self.family_gift:
            product_search.append(GIFT_PRODUCTS_REF[2])
        if self.project_gift:
            product_search.append(GIFT_PRODUCTS_REF[3])
        if self.graduation_gift:
            product_search.append(GIFT_PRODUCTS_REF[4])
        if not product_search:
            raise odooWarning(_("Please select at least one gift type."))

        products = self.env["product.product"].search(
            [("default_code", "in", product_search)]
        )
        data = {
            "doc_ids": self.env.context.get("active_ids"),
            "product_ids": products.ids,
        }
        records = self.env[self.env.context.get("active_model")].browse(data["doc_ids"])
        report_name = "report_compassion.report_" + self.paper_format.split(".")[1]
        report_ref = self.env.ref(report_name)
        if self.pdf:
            name = records.name if len(records) == 1 else _("gift payment slips")
            self.pdf_name = name + ".pdf"
            pdf_data = report_ref.with_context(
                must_skip_send_to_printer=True
            )._render_qweb_pdf(data["doc_ids"], data=data)[0]
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
        return report_ref.report_action(data["doc_ids"], data=data, config=False)
