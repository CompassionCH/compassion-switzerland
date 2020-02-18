##############################################################################
#
#    Copyright (C) 2019 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64

from odoo import models, _


class PartnerCommunication(models.Model):
    """
    Not used yet. This could be useful to join the PDF of the invoice
    to the email.
    """

    _inherit = "partner.communication.job"

    def get_report_online_invoice(self):
        """
        Attachment function that adds the invoice report to the communication.
        :return: dict {attachment_name: [report_name, pdf_data]}
        """
        attachments = {}
        report = "l10n_ch_payment_slip.one_slip_per_page_from_invoice"
        for invoice in self.get_objects():
            name = _("Invoice") + " " + (invoice.origin or invoice.number) + ".pdf"
            attachments[name] = [
                report,
                base64.b64encode(self.env["report"].get_pdf(invoice.ids, report,)),
            ]
        return attachments
