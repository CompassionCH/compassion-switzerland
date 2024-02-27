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
import logging
import os
import tempfile
from io import BytesIO
from zipfile import ZipFile

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Limit number of photos to handle at a time to avoid memory issues
NUMBER_LIMIT = 80

try:
    from pdf2image import convert_from_path
except ImportError:
    _logger.debug("Can not `import pdf2image`.")


class CompassionHold(models.TransientModel):
    _inherit = "mail.activity.mixin"
    _name = "child.order.picture.wizard"

    sponsorship_ids = fields.Many2many(
        "recurring.contract",
        string="New biennials",
        readonly=True,
        default=lambda s: s._get_sponsorships(),
    )
    filename = fields.Char(default="child_photos.zip")
    download_data = fields.Binary(readonly=True)

    @api.model
    def _get_sponsorships(self):
        model = "recurring.contract"
        if self.env.context.get("active_model") == model:
            ids = self.env.context.get("active_ids")
            if ids:
                return self.env[model].browse(ids)
        elif self.env.context.get("order_menu"):
            return self.env[model].search(self._needaction_domain_get())
        return False

    @api.multi
    def order_pictures(self):
        return self._get_pictures()

    @api.multi
    def print_pictures(self):
        return self._get_pictures(_print=True)

    @api.multi
    def _get_pictures(self, _print=False):
        """
        Generate child pictures with white frame and make a downloadable
        ZIP file or generate a report for printing.
        :param _print: Set to true for PDF generation instead of ZIP file.
        :return: Window Action
        """
        sponsorships = self.sponsorship_ids[:NUMBER_LIMIT]
        if _print:
            report = self.env.ref(
                "partner_communication_switzerland.report_child_picture"
            )
            res = report.report_action(sponsorships.mapped("child_id.id"), config=False)
        else:
            self.download_data = self._make_zip()
            res = {
                "type": "ir.actions.act_window",
                "view_type": "form",
                "view_mode": "form",
                "res_id": self.id,
                "res_model": self._name,
                "context": self.env.context,
                "target": "new",
            }
        sponsorships.write({"order_photo": False})
        # Log a note to recover the sponsorships in case the ZIP is lost
        for s in sponsorships:
            s.message_post("Picture ordered.")
        return res

    @api.multi
    def _make_zip(self):
        """
        Create a zip file with all pictures
        :param self:
        :return: b64_data of the generated zip file
        """
        zip_buffer = BytesIO()
        children = self.mapped("sponsorship_ids.child_id")[:NUMBER_LIMIT]
        with ZipFile(zip_buffer, "w") as zip_data:
            report_ref = self.env.ref(
                "partner_communication_switzerland.report_child_picture"
            ).with_context(must_skip_send_to_printer=True)
            pdf_data = report_ref.render_qweb_pdf(
                children.ids, data={"doc_ids": children.ids}
            )[0]
            pdf_temp_file, pdf_temp_file_name = tempfile.mkstemp()
            os.write(pdf_temp_file, pdf_data)
            pages = convert_from_path(pdf_temp_file_name)
            for page_id, page in enumerate(pages):
                child = self.env["compassion.child"].browse(children.ids[page_id])
                fname = str(child.sponsor_ref) + "_" + str(child.local_id) + ".jpg"

                page.save(os.path.join("/tmp/", fname), "JPEG")
                file_byte = open(os.path.join("/tmp/", fname), "br").read()
                zip_data.writestr(fname, file_byte)

        zip_buffer.seek(0)
        return base64.b64encode(zip_buffer.read())

    @api.model
    def _needaction_domain_get(self):
        return [
            ("order_photo", "=", True),
            ("state", "not in", [("terminated", "cancelled")]),
        ]

    @api.model
    def _needaction_count(self, domain=None):
        """Get the number of actions uid has to perform."""
        return self.env["recurring.contract"].search_count(
            self._needaction_domain_get()
        )
