##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64

from odoo import models, api, _


class CommunicationJob(models.Model):
    _inherit = "partner.communication.job"

    @api.multi
    def get_trip_down_payment_attachment(self):
        """
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        registration = self.get_objects()
        product = registration.event_ticket_id.product_id
        report_vals = {
            'doc_ids': registration.partner_id.ids,
            'product_id': product.id,
            'background': True,
            'preprinted': False,
            'amount': registration.event_ticket_id.price
        }

        report_name = 'report_compassion.bvr_fund'
        report_ref = self.env.ref('report_compassion.report_bvr_fund')

        pdf_data = base64.encodebytes(report_ref.render_qweb_pdf(
            registration.partner_id.ids, report_vals)[0])

        return {
            _('down_payment.pdf'): [report_name, pdf_data]
        }

    @api.multi
    def get_trip_payment_attachment(self):
        """
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        self.ensure_one()
        registration = self.get_objects()
        invoice = registration.group_visit_invoice_id
        product = self.env['product.product'].search([
            ('product_tmpl_id', '=', self.env.ref(
                'website_event_compassion.product_template_trip_price').id)
        ])
        event_name = registration.compassion_event_id.name
        report_vals = {
            'doc_ids': registration.partner_id.ids,
            'product_id': product.id,
            'background': True,
            'preprinted': False,
            'amount': invoice.amount_total,
            'communication': event_name
        }
        report_name = 'report_compassion.bvr_fund'
        pdf_data = base64.b64encode(self.env['report'].with_context(
            must_skip_send_to_printer=True).render_qweb_pdf(
            registration.partner_id.ids, report_name, data=report_vals))
        return {
            event_name + '.pdf': [report_name, pdf_data]
        }
