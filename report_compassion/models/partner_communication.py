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


class PartnerCommunication(models.Model):
    """ Add fields for retrieving values for communications.
    Send a communication when a major revision is received.
    """

    _inherit = "partner.communication.job"

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    product_id = fields.Many2one("product.product", "QR Bill for fund", readonly=False)
    display_pp = fields.Boolean(
        string="Display PP",
        help="If not set, the PP is not printed upper the address.",
        default=True,
    )

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def send(self):
        """
        Change the report for communications to print with BVR
        Update the count of succes story prints when sending a receipt.
        :return: True
        """
        bvr_to_send = self.filtered(lambda j: j.send_mode == "digital" and j.product_id)
        bvr_to_print = self.filtered(
            lambda j: j.send_mode == "physical" and j.product_id
        )
        bvr_both = self.filtered(lambda j: j.send_mode == "both" and j.product_id)

        if bvr_both and self.env.context.get("origin") == "both_email":
            for bvr in bvr_both:
                # email part
                self._put_bvr_in_attachments(bvr)

            super(PartnerCommunication, bvr_both).send()

        if bvr_to_send:
            for bvr in bvr_to_send:
                self._put_bvr_in_attachments(bvr)
            super(PartnerCommunication, bvr_to_send).send()

        if bvr_to_print:
            super(PartnerCommunication, bvr_to_print).send()

        return super(
            PartnerCommunication, self - bvr_both - bvr_to_print - bvr_to_send
        ).send()

    def _put_bvr_in_attachments(self, bvr):
        pdf_download = self._generate_pdf_data(bvr)
        return self._create_and_add_attachment(bvr, pdf_download)

    def _create_and_add_attachment(self, bvr, datas):
        attachment = self.env["ir.attachment"].create(
            {"name": bvr.report_id.name, "type": "binary", "datas": datas}
        )
        comm_attachment = self.env["partner.communication.attachment"].create(
            {
                "name": bvr.report_id.name,
                "report_name": "report_compassion.a4_bvr",
                "communication_id": bvr.id,
                "attachment_id": attachment.id,
            }
        )
        bvr.write({"attachment_ids": [(4, comm_attachment.id)]})
        return bvr

    def _generate_pdf_data(self, bvr):
        data = {
            "doc_ids": bvr.id,
            "product_id": bvr.product_id.id,
        }
        report_ref = self.env.ref("report_compassion.report_compassion_qr_slip")
        pdf_data = report_ref.with_context(
            must_skip_send_to_printer=True
        ).render_qweb_pdf(bvr.id, data=data)[0]
        return base64.encodebytes(pdf_data)

    @api.model
    def _get_default_vals(self, vals, default_vals=None):
        if default_vals is None:
            default_vals = []
        default_vals.append("display_pp")
        return super()._get_default_vals(vals, default_vals)
