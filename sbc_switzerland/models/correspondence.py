##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import sys
import base64
import logging
from importlib import reload

from io import BytesIO

from . import translate_connector

from odoo import models, api, fields, _
from odoo.tools.config import config
from odoo.exceptions import UserError
from odoo.addons.sbc_compassion.models.correspondence_page import \
    BOX_SEPARATOR


logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileReader, PdfFileWriter
    from smb.SMBConnection import SMBConnection
except ImportError:
    logger.warning("Please install pyPdf and smb.")


class S2BGenerator(models.Model):
    _inherit = 'correspondence.s2b.generator'

    selection_domain = fields.Char(
        default="[('partner_id.category_id', '=', 23),"
                " ('state', '=', 'active'), ('child_id', '!=', False)]"
    )


class Correspondence(models.Model):
    """ This class intercepts a letter before it is sent to GMC.
        Letters are pushed to local translation platform if needed.
        """

    _inherit = 'correspondence'

    src_translation_lang_id = fields.Many2one(
        'res.lang.compassion', 'Source of translation')

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Create a message for sending the CommKit after be translated on
             the local translate plaform.
        """
        if vals.get('direction') == "Beneficiary To Supporter":
            correspondence = super().create(vals)
        else:
            sponsorship = self.env['recurring.contract'].browse(
                vals['sponsorship_id'])

            original_lang = self.env['res.lang.compassion'].browse(
                vals.get('original_language_id'))

            # TODO Remove this fix when HAITI case is resolved
            # For now, we switch French to Creole for avoiding translation
            if 'HA' in sponsorship.child_id.local_id:
                french = self.env.ref(
                    'child_compassion.lang_compassion_french')
                creole = self.env.ref(
                    'child_compassion.lang_compassion_haitien_creole')
                if original_lang == french:
                    vals['original_language_id'] = creole.id

            # Languages the office/region understand
            office = sponsorship.child_id.project_id.field_office_id
            language_ids = office.spoken_language_ids + office.translated_language_ids

            if original_lang.translatable and original_lang not in language_ids:
                correspondence = super(Correspondence, self.with_context(
                    no_comm_kit=True)).create(vals)
                correspondence.send_local_translate()
            else:
                correspondence = super().create(vals)

        # Swap pages for L3 layouts as we scan in wrong order
        if correspondence.template_id.layout == 'CH-A-3S01-1' and \
                correspondence.source in ('letter', 'email') and \
                correspondence.store_letter_image:
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
                correspondence.write({
                    'letter_image': base64.b64encode(letter_data.read())
                })

        return correspondence

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    @api.multi
    def process_letter(self):
        """ Called when B2S letter is Published. Check if translation is
         needed and upload to translation platform. """
        letters_to_send = self.env[self._name]
        intro_letter = self.env.ref(
            'sbc_compassion.correspondence_type_new_sponsor')
        for letter in self:
            # if letter.original_language_id in \
            #         letter.supporter_languages_ids or \
            if (letter.beneficiary_language_ids &
                    letter.supporter_languages_ids) or \
                    letter.has_valid_language:
                if intro_letter in letter.communication_type_ids and not \
                        letter.sponsorship_id.send_introduction_letter:
                    continue
                if super(Correspondence, letter).process_letter():
                    letters_to_send += letter

            else:
                letter.download_attach_letter_image()
                letter.send_local_translate()

        letters_to_send.send_communication()
        return True

    @api.multi
    def send_local_translate(self):
        """
        Sends the letter to the local translation platform.
        :return: None
        """
        self.ensure_one()
        child = self.sponsorship_id.child_id

        # Specify the src and dst language
        src_lang, dst_lang = self._get_translation_langs()

        # File name
        sponsor = self.sponsorship_id.partner_id
        file_name = "_".join(
            (child.local_id, sponsor.ref, str(self.id))) + '.pdf'

        # Send letter to local translate platform
        tc = translate_connector.TranslateConnect()
        text_id = tc.upsert_text(
            self, file_name, tc.get_lang_id(src_lang),
            tc.get_lang_id(dst_lang))
        translation_id = tc.upsert_translation(text_id, self)
        tc.upsert_translation_status(translation_id)

        # Transfer file on the NAS
        self._transfer_file_on_nas(file_name)
        self.write({
            'state': 'Global Partner translation queue',
            'src_translation_lang_id': src_lang.id,
        })

    @api.model
    def fix_priority(self):
        tc = translate_connector.TranslateConnect()
        supporter_lettres = self.search([
            ('direction', '=', 'Beneficiary To Supporter'),
            ('state', '=', 'Global Partner translation queue'),
            ('scanned_date', '<', '2017-11-01'),
            ('scanned_date', '>=', '2017-10-01'),
        ])
        logger.info(len(supporter_lettres))
        cpt = 1
        for letter in supporter_lettres:
            translation_id = tc.upsert("translation", {
                'letter_odoo_id': letter.id,
                'createdat': letter.scanned_date
            })
            text_id = tc.select_one(
                "SELECT text_id FROM translation WHERE id = %s", [
                    translation_id]).get('text_id')
            if text_id:
                tc.upsert("text", {
                    'id': text_id,
                    'priority_id': 3
                })
                logger.info(str(cpt) + '/' + str(len(supporter_lettres)))
            else:
                logger.info("Not found letter")
            cpt += 1
        return True

    @api.model
    def clean_translate(self):
        tc = translate_connector.TranslateConnect()
        letters = self.search([
            ('state', '!=', 'Global Partner translation queue')
        ])
        for letter in letters:
            translation = tc.select_one(
                "SELECT t.id as id, s.id as status "
                "FROM translation t join translation_status s on "
                "s.translation_id = t.id "
                "WHERE t.letter_odoo_id = %s AND s.status_id = 1", [letter.id]
            )
            letter_id = translation.get('id')
            status = translation.get('status')
            if letter_id and status:
                tc.update_translation_to_treated(letter_id)
                tc.upsert('translation_status', {'id': status, 'status_id': 3})
                logger.info("Correct " + str(letter.id))
        return True

    @api.model
    def check_missing_translate(self):
        tc = translate_connector.TranslateConnect()
        letters = self.search([
            ('state', '=', 'Global Partner translation queue')
        ])
        logger.info(f"Found {len(letters)} letters to translate.")
        for letter in letters:
            letter_id = tc.select_one(
                "SELECT id FROM translation WHERE letter_odoo_id = %s",
                [letter.id]).get('id')
            if not letter_id:
                letter.send_local_translate()
                logger.info("Send missing: " + letter.kit_identifier)
        return True

    @api.multi
    def remove_local_translate(self):
        """
        Remove a letter from local translation platform and change state of
        letter in Odoo
        :return: None
        """
        self.ensure_one()
        tc = translate_connector.TranslateConnect()
        tc.remove_translation_with_odoo_id(self.id)
        if self.direction == 'Supporter To Beneficiary':
            self.state = 'Received in the system'
            self.create_commkit()
        else:
            self.state = 'Published to Global Partner'

    @api.multi
    def update_translation(self, translate_lang, translate_text, translator,
                           src_lang):
        """
        Puts the translated text into the correspondence.
        :param translate_lang: code_iso of the language of the translation
        :param translate_text: text of the translation
        :param translator: reference of the translator
        :param src_lang: code_iso of the source language of translation
        :return: None
        """
        self.ensure_one()
        translate_lang_id = self.env['res.lang.compassion'].search(
            [('code_iso', '=', translate_lang)]).id
        src_lang_id = self.env['res.lang.compassion'].search(
            [('code_iso', '=', src_lang)]).id
        translator_partner = self.env['res.partner'].search([
            ('ref', '=', translator)])

        letter_vals = {
            'translation_language_id': translate_lang_id,
            'translator_id': translator_partner.id,
            'src_translation_lang_id': src_lang_id,
        }
        if self.direction == 'Supporter To Beneficiary':
            state = 'Received in the system'

            # Compute the target text
            target_text = 'english_text'
            if translate_lang != 'eng':
                target_text = 'translated_text'

            # Remove #BOX# in the text, as supporter letters don't have boxes
            translate_text = translate_text.replace(BOX_SEPARATOR, '\n')
        else:
            state = 'Published to Global Partner'
            target_text = 'translated_text'

        # Check that layout L4 translation gets on second page
        if self.template_id.layout == 'CH-A-4S01-1' and \
                not translate_text.startswith('#PAGE#'):
            translate_text = '#PAGE#' + translate_text
        letter_vals.update({
            target_text: translate_text.replace('\r', ''),
            'state': state,
        })
        self.write(letter_vals)

        # Activate advocate translator
        translator_partner.advocate_details_id.with_context(
            skip_translation_platform_update=True).set_active()

        # Send to GMC
        if self.direction == 'Supporter To Beneficiary':
            self.create_commkit()
        else:
            # Recompose the letter image and process letter
            if super().process_letter():
                self.send_communication()

    def merge_letters(self):
        """ We have issues with letters that we send and we have an error.
        Then when we try to send it again, we have a duplicate letter because
        GMC created another letter on our system. We use this method to fix
        it and merge the two letters.
        """
        assert len(self) == 2 and len(self.mapped('child_id')) == 1
        direction = list(set(self.mapped('direction')))
        assert len(direction) == 1 and direction[0] == \
            'Supporter To Beneficiary'
        gmc_letter = self.filtered('kit_identifier')
        our_letter = self - gmc_letter
        assert len(our_letter) == 1 and len(gmc_letter) == 1
        vals = {
            'kit_identifier': gmc_letter.kit_identifier,
            'state': gmc_letter.state
        }
        gmc_letter.kit_identifier = False
        gmc_letter.unlink()
        return our_letter.write(vals)

    ##########################################################################
    #                             PRIVATE METHODS                            #
    ##########################################################################
    def _get_translation_langs(self):
        """
        Finds the source_language et destination_language suited for
        translation of the given letter.

        S2B:
            - src_lang is the original language of the letter
            - dst_lang is the lang of the child if translatable, else
              english

        B2S:
            - src_lang is the original language if translatable, else
              english
            - dst_lang is the main language of the sponsor
        :return: src_lang, dst_lang
        :rtype: res.lang.compassion, res.lang.compassion
        """
        self.ensure_one()
        src_lang = False
        dst_lang = False
        if self.direction == 'Supporter To Beneficiary':
            # Check that the letter is not yet sent to GMC
            if self.kit_identifier:
                raise UserError(_("Letter already sent to GMC cannot be "
                                  f"translated! [{self.kit_identifier}]"))

            src_lang = self.original_language_id
            child_langs = self.beneficiary_language_ids.filtered(
                'translatable')
            if child_langs:
                dst_lang = child_langs[-1]
            else:
                dst_lang = self.env.ref(
                    'child_compassion.lang_compassion_english')

        elif self.direction == 'Beneficiary To Supporter':
            if self.original_language_id and \
                    self.original_language_id.translatable:
                src_lang = self.original_language_id
            else:
                src_lang = self.env.ref(
                    'child_compassion.lang_compassion_english')
            dst_lang = self.supporter_languages_ids.filtered(
                lambda lang: lang.lang_id and lang.lang_id.code ==
                self.partner_id.lang)

        return src_lang, dst_lang

    def _transfer_file_on_nas(self, file_name):
        """
        Puts the letter file on the NAS folder for the translation platform.
        :return: None
        """
        self.ensure_one()
        # Retrieve configuration
        smb_user = config.get('smb_user')
        smb_pass = config.get('smb_pwd')
        smb_ip = config.get('smb_ip')
        smb_port = int(config.get('smb_port', 0))
        if not (smb_user and smb_pass and smb_ip and smb_port):
            raise Exception('No config SMB in file .conf')

        # Copy file in the imported letter folder
        smb_conn = SMBConnection(smb_user, smb_pass, 'openerp', 'nas')
        if smb_conn.connect(smb_ip, smb_port):
            file_ = BytesIO(self.get_image())
            nas_share_name = self.env.ref(
                'sbc_switzerland.nas_share_name').value

            nas_letters_store_path = self.env.ref(
                'sbc_switzerland.nas_letters_store_path').value + file_name
            smb_conn.storeFile(nas_share_name,
                               nas_letters_store_path, file_)

            logger.info(f'File {self.file_name} store on NAS with success')
        else:
            raise UserError(_('Connection to NAS failed'))

    # CRON Methods
    ##############
    @api.model
    def check_local_translation_done(self):
        reload(sys)
        tc = translate_connector.TranslateConnect()
        letters_to_update = tc.get_translated_letters()

        for letter in letters_to_update:
            try:
                logger.info(
                    f".....CHECK TRANSLATION FOR LETTER {letter['letter_odoo_id']}"
                )
                correspondence = self.browse(letter["letter_odoo_id"])
                if correspondence.exists():
                    correspondence.update_translation(
                        letter["target_lang"], letter["text"],
                        letter["translator"],
                        letter["src_lang"]
                    )
                tc.update_translation_to_treated(letter["id"])
            except:
                logger.error(
                    "Error fetching a translation on translation platform",
                    exc_info=True
                )
        return True
