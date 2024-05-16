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
    @api.model
    def create(self, vals):
        correspondence = super().create(vals)
        # Swap pages for L3 layouts as we scan in wrong order
        if (
            correspondence.template_id.layout == "CH-A-3S01-1"
            and correspondence.source in ("letter", "email")
            and correspondence.store_letter_image
        ):
            input_pdf = PdfFileReader(BytesIO(correspondence.get_image()))
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
                    {"letter_image": base64.b64encode(letter_data.read())}
                )

        return correspondence

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
