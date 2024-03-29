##############################################################################
#
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Sylvain Losey <sylvainlosey@gmail.com>
#    @author: Théo Nikles <theo.nikles@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64

from odoo import api, models, _
from odoo.addons.sponsorship_compassion.models.product_names import GIFT_REF


class MailComposer(models.TransientModel):
    _inherit = "mail.compose.message"

    @api.multi
    def onchange_template_id(self, template_id, composition_mode, model, res_id):
        """
        Add gift payment slips for "Gift/Payment slip" and "Christmas Gift Fund"
        """
        result = super().onchange_template_id(template_id, composition_mode,
                                              model, res_id)

        # Clear previous attachments
        self.attachment_ids = None

        # Add gift payment slips
        template = self.env["mail.template"].browse(template_id)
        template_name = template.with_context(lang="en_US").name

        if not self.partner_ids:
            return result
        partner = self.partner_ids[0]
        sponsorships = partner.sponsorship_ids

        if template_name == "Gift/Payment slip" and sponsorships:
            refs = [GIFT_REF[0], GIFT_REF[1], GIFT_REF[2]]
            report = self.env.ref("report_compassion.report_3bvr_gift_sponsorship")
            payment_slips = self.get_payment_slips(refs, report, sponsorships.ids)
            result["value"]["attachment_ids"] = payment_slips.ids

        if template_name == "Christmas Gift Fund":
            refs = ["noel"]
            report = self.env.ref("report_compassion.report_bvr_fund")
            payment_slips = self.get_payment_slips(refs, report, partner.id)
            result["value"]["attachment_ids"] = payment_slips.ids

        return result

    def get_payment_slips(self, refs, report, doc_ids):
        """
        Returns the pdf of selected gift payment slips
        :return: "ir.attachment" instance
        """
        product = self.env["product.product"].search([("default_code", "in", refs)])
        data = {
            "product_ids": product.ids,
            "product_id": product.ids,
            "background": True,
        }
        pdf = report.with_context(must_skip_send_to_printer=True).render_qweb_pdf(
            doc_ids, data=data
        )
        file_name = _("gift payment slips") + ".pdf"

        return self.env['ir.attachment'].create({
            'name': file_name,
            'datas_fname': file_name,
            'datas': base64.encodebytes(pdf[0]),
        })
