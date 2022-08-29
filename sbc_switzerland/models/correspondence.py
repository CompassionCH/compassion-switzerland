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


from odoo import models, api, fields

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
    """ This class intercepts a letter before it is sent to GMC.
        Letters are pushed to local translation platform if needed.
        """

    _inherit = "correspondence"

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        if vals.get("direction") == "Supporter To Beneficiary":
            sponsorship = self.env["recurring.contract"].browse(vals["sponsorship_id"])

            original_lang = self.env["res.lang.compassion"].browse(
                vals.get("original_language_id")
            )

            # TODO Remove this fix when HAITI case is resolved
            # For now, we switch French to Creole for avoiding translation
            if "HA" in sponsorship.child_id.local_id:
                french = self.env.ref("advanced_translation.lang_compassion_french")
                creole = self.env.ref("advanced_translation.lang_compassion_haitien_creole")
                if original_lang == french:
                    vals["original_language_id"] = creole.id

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
    @api.multi
    def process_letter(self):
        """ Called when B2S letter is Published. Check if translation is
         needed and upload to translation platform. """
        intro_letter = self.env.ref("sbc_compassion.correspondence_type_new_sponsor")
        for letter in self:
            if intro_letter in letter.communication_type_ids and not \
                    letter.sponsorship_id.send_introduction_letter:
                continue
            super(Correspondence, letter).process_letter()
        self.filtered(lambda l: l.state == "Published to Global Partner").send_communication()
        return True

    def merge_letters(self):
        """ We have issues with letters that we send and we have an error.
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
