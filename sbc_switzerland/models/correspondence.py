##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import base64
import logging
from io import BytesIO

from odoo import api, fields, models

logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileReader, PdfFileWriter
except ImportError:
    logger.warning("Please install pyPdf.")


class S2BGenerator(models.Model):
    _inherit = "correspondence.s2b.generator"

    selection_domain = fields.Char(
        default="[('partner_id.category_id', '=', 23),"
        " ('state', '=', 'active'), ('child_id', '!=', False)]"
    )


class Correspondence(models.Model):
    _inherit = "correspondence"

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model_create_multi
    def create(self, vals):
        correspondences = super().create(vals)
        # Swap pages for L3 layouts as we scan in wrong order
        for correspondence in correspondences.filtered(
            lambda c: c.template_id.layout == "CH-A-3S01-1"
            and c.source in ("letter", "email")
            and c.sponsor_letter_scan
            and c.direction == "Supporter To Beneficiary"
        ):
            input_pdf = PdfFileReader(BytesIO(correspondence.get_pdf()))
            output_pdf = PdfFileWriter()
            nb_pages = input_pdf.numPages
            if nb_pages >= 2:
                output_pdf.addPage(input_pdf.getPage(1))
                output_pdf.addPage(input_pdf.getPage(0))
                if nb_pages > 2:
                    for i in range(2, nb_pages):
                        output_pdf.addPage(input_pdf.getPage(i))
                letter_data = BytesIO()
                output_pdf.write(letter_data)
                letter_data.seek(0)
                correspondence.write(
                    {"sponsor_letter_scan": base64.b64encode(letter_data.read())}
                )
        return correspondences

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def merge_letters(self):
        """We have issues with letters that we send and we have an error.
        Then when we try to send it again, we have a duplicate letter because
        GMC created another letter on our system. We use this method to fix
        it and merge the two letters.
        """
        assert len(self) == 2 and len(self.mapped("child_id")) == 1
        direction = list(set(self.mapped("direction")))
        assert len(direction) == 1 and direction[0] == "Supporter To Beneficiary"
        gmc_letter = self.filtered("kit_identifier")
        our_letter = self - gmc_letter
        assert len(our_letter) == 1 and len(gmc_letter) == 1
        vals = {"kit_identifier": gmc_letter.kit_identifier, "state": gmc_letter.state}
        gmc_letter.kit_identifier = False
        gmc_letter.unlink()
        return our_letter.write(vals)

    def split_letter(self):
        # Letters longer than 15 pages should be split
        self.ensure_one()
        max_page_num = 15
        input_pdf = PdfFileReader(BytesIO(self.get_pdf()))
        nb_pages = input_pdf.numPages
        letters = self
        pages = self.mapped("page_ids")
        assert nb_pages == len(pages)
        if nb_pages > max_page_num:
            for start_page in range(0, nb_pages, max_page_num):
                output_pdf = PdfFileWriter()
                for i in range(start_page, min(start_page + max_page_num, nb_pages)):
                    output_pdf.addPage(input_pdf.getPage(i))
                letter_data = BytesIO()
                output_pdf.write(letter_data)
                letter_data.seek(0)
                if start_page == 0:
                    self.write(
                        {"sponsor_letter_scan": base64.b64encode(letter_data.read())}
                    )
                    continue
                letter_vals = self.copy_data()[0]
                letter_vals.update(
                    {
                        "sponsor_letter_scan": base64.b64encode(letter_data.read()),
                        "page_ids": [
                            (6, 0, pages[start_page : start_page + max_page_num].ids)
                        ],
                    }
                )
                letters += self.env["correspondence"].create(letter_vals)
            self.write(
                {
                    "page_ids": [(6, 0, pages[:max_page_num].ids)],
                }
            )
        return {
            "type": "ir.actions.act_window",
            "name": "Split Letters",
            "res_model": "correspondence",
            "view_mode": "list,form",
            "domain": [("id", "in", letters.ids)],
        }

    def assign_supervisor(self):
        """
        This method assigns a supervisor for a letter.
        Can be inherited to customize by whom the letters need to be checked.
        We assign the letter to the SDS team by default
        """
        translation_supervisor = (
            self.env["res.users"].sudo().search([("email", "=", "sds@compassion.ch")])
        )
        (self - self.filtered("translation_supervisor_id")).write(
            {"translation_supervisor_id": translation_supervisor.id}
        )
        return True
