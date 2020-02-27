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
    _inherit = 'partner.communication.job'

    ##########################################################################
    #                                 FIELDS                                 #
    ##########################################################################
    product_id = fields.Many2one('product.product', 'A4 + payment slip')
    preprinted = fields.Boolean(
        help='Enable if you print on a payment slip that already has company '
             'information printed on it.'
    )
    display_pp = fields.Boolean(
        string='Display PP',
        help='If not set, the PP is not printed upper the address.',
        default=True
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
        bvr_to_send = self.filtered(lambda j: j.send_mode == 'digital'
                                    and j.product_id)
        bvr_to_print = self.filtered(lambda j: j.send_mode == 'physical'
                                     and j.product_id)
        bvr_both = self.filtered(lambda j: j.send_mode == 'both'
                                 and j.product_id)

        if bvr_both:
            for bvr in bvr_both:
                # email part
                pdf_download = self._generate_pdf_data(bvr, background=bvr.send_mode == 'digital')
                bvr.attachment_ids.unlink()
                self._create_and_add_attachment(bvr, pdf_download)

                # print part
                if bvr.report_id == self.env.ref('report_compassion.report_a4_bvr'):
                    bvr.write({'report_id': self.env.ref(
                        'report_compassion.report_a4_bvr').id})  # TODO what must we do here ?
            return super(PartnerCommunication, bvr_both).send()

        if bvr_to_send:
            for bvr in bvr_to_send:
                pdf_download = self._generate_pdf_data(bvr, background=True)
                bvr.attachment_ids.unlink()
                self._create_and_add_attachment(bvr, pdf_download)
            return super(PartnerCommunication, bvr_to_send).send()

        if bvr_to_print:
            for bvr in bvr_to_print:
                if bvr.report_id == self.env.ref('report_compassion.report_a4_bvr'):
                    bvr.write({'report_id': self.env.ref(
                        'report_compassion.report_a4_bvr').id})  # TODO what must we do here ?
                else:
                    pdf_download = self._generate_pdf_data(bvr, background=False)
                    bvr.attachment_ids.unlink()
                    self._create_and_add_attachment(bvr, pdf_download)
            return super(PartnerCommunication, bvr_to_print).send()

    def _create_and_add_attachment(self, bvr, datas):
        attachment = self.env['ir.attachment'].create({
            "name": bvr.report_id.name,
            "type": "binary",
            "datas": datas
        })
        bvr.write({
            'attachment_ids': [[0, 0, {
                "name": bvr.report_id.name,
                "report_name": "report_compassion.a4_bvr",
                "communication_id": bvr.id,
                "attachment_id": attachment.id
            }]]
        })
        return bvr

    def _generate_pdf_data(self, bvr, background):
        data = {
            'doc_ids': bvr.id,
            'product_id': bvr.product_id.id,
            'background': background
        }
        report_ref = self.env.ref('report_compassion.report_a4_bvr')
        pdf_data = report_ref.report_action(bvr, data=data)
        return base64.encodebytes(
            report_ref.render_qweb_pdf(
                pdf_data['data']['doc_ids'], pdf_data['data'])[0])

    @api.model
    def _get_default_vals(self, vals, default_vals=None):
        if default_vals is None:
            default_vals = []
        default_vals.append('display_pp')
        return super()._get_default_vals(
            vals, default_vals)
