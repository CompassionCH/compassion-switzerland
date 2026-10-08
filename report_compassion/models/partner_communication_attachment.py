##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from odoo import models

CERTIFICATE = "report_compassion.ending_sponsorship_certificate"
COVER = "report_compassion.blank_communication"


class PartnerCommunicationAttachment(models.Model):
    _inherit = "partner.communication.attachment"

    def rerender_certificate_pdf(self):
        """Re-render the PDF of ending certificates and blank covers of unsent
        communications. Used by the 18.0.1.0.7 migration (T3500).
        The generating methods live in partner_communication_switzerland."""
        for attachment in self:
            job = attachment.communication_id
            if job.state not in ("pending", "failure"):
                continue
            job = job.with_context(
                lang=job.partner_id.lang, must_skip_send_to_printer=True
            )
            if attachment.report_name == COVER:
                binaries = job.get_blank_communication_attachment()
            elif job.config_id.attachments_function == (
                "get_end_sponsorship_certificate_new_version"
            ):
                binaries = job.get_end_sponsorship_certificate_new_version()
            else:
                binaries = job.get_end_sponsorship_certificate()
            attachment.attachment_id.datas = next(iter(binaries.values()))[1]
        return True
