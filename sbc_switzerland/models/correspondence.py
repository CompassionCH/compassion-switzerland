# -*- coding: utf-8 -*-
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

from io import BytesIO

from . import translate_connector

from odoo import models, api, registry, fields, _
from odoo.tools.config import config
from odoo.exceptions import UserError
from odoo.addons.sbc_compassion.models.correspondence_page import \
    BOX_SEPARATOR


logger = logging.getLogger(__name__)

try:
    from pyPdf.pdf import PdfFileReader, PdfFileWriter
    from smb.SMBConnection import SMBConnection
except ImportError:
    logger.warning("Please install pyPdf and smb.")


class S2BGenerator(models.Model):
    _inherit = 'correspondence.s2b.generator'

    selection_domain = fields.Char(
        default="[('partner_id.category_id', '=', 23),"
                " ('state', '=', 'active')]"
    )


class Correspondence(models.Model):
    """ This class intercepts a letter before it is sent to GMC.
        Letters are pushed to local translation platform if needed.
        """

    _inherit = 'correspondence'

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################
    @api.model
    def create(self, vals):
        """ Create a message for sending the CommKit after be translated on
             the local translate plaform.
        """
        if vals.get('direction') == "Beneficiary To Supporter":
            correspondence = super(Correspondence, self).create(vals)
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

            if original_lang.translatable and original_lang not in sponsorship\
                    .child_id.project_id.field_office_id.spoken_language_ids:
                correspondence = super(Correspondence, self.with_context(
                    no_comm_kit=True)).create(vals)
                correspondence.send_local_translate()
            else:
                correspondence = super(Correspondence, self).create(vals)

        # Swap pages for L3 layouts as we scan in wrong order
        if correspondence.template_id.layout == 'CH-A-3S01-1' and \
                correspondence.source != 'compassion':
            input_pdf = PdfFileReader(BytesIO(base64.b64decode(
                correspondence.letter_image)))
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
        for letter in self:
            # if letter.original_language_id in \
            #         letter.supporter_languages_ids or \
            if (letter.beneficiary_language_ids &
                    letter.supporter_languages_ids) or \
                    letter.has_valid_language:
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
        src_lang_id, dst_lang_id = self._get_translation_langs()

        # File name
        sponsor = self.sponsorship_id.partner_id
        # TODO : replace by global_id once all ids are fetched
        file_name = "_".join(
            (child.local_id, sponsor.ref, str(self.id))) + '.pdf'

        # Send letter to local translate platform
        tc = translate_connector.TranslateConnect()
        text_id = tc.upsert_text(
            self, file_name, tc.get_lang_id(src_lang_id),
            tc.get_lang_id(dst_lang_id))
        translation_id = tc.upsert_translation(text_id, self)
        tc.upsert_translation_status(translation_id)

        # Transfer file on the NAS
        self._transfer_file_on_nas(file_name)
        self.state = 'Global Partner translation queue'

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
            text_id = tc.selectOne(
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
            translation = tc.selectOne(
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
        logger.info("Found {} letters to transalte.".format(str(len(letters))))
        for letter in letters:
            letter_id = tc.selectOne(
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
    def update_translation(self, translate_lang, translate_text, translator):
        """
        Puts the translated text into the correspondence.
        :param translate_lang: code_iso of the language of the translation
        :param translate_text: text of the translation
        :param translator: reference of the translator
        :return: None
        """
        self.ensure_one()
        translate_lang_id = self.env['res.lang.compassion'].search(
            [('code_iso', '=', translate_lang)]).id
        translator_partner = self.env['res.partner'].search([
            ('ref', '=', translator)])
        local_id = self.child_id.local_id

        if self.direction == 'Supporter To Beneficiary':
            state = 'Received in the system'
            target_text = 'original_text'
            language_field = 'original_language_id'
            # Remove #BOX# in the text, as supporter letters don't have boxes
            translate_text = translate_text.replace(BOX_SEPARATOR, '\n')
            # TODO Remove this fix when HAITI case is resolved
            # For now we switch French to Creole
            if 'HA' in local_id:
                french = self.env.ref(
                    'child_compassion.lang_compassion_french')
                creole = self.env.ref(
                    'child_compassion.lang_compassion_haitien_creole')
                if translate_lang_id == french.id:
                    translate_lang_id = creole.id
        else:
            state = 'Published to Global Partner'
            target_text = 'translated_text'
            language_field = 'translation_language_id'
            # TODO Remove this when new translation tool is working
            # Workaround to avoid overlapping translation : everything goes
            # in L6 template
            if 'HO' not in local_id and 'RW' not in local_id:
                self.b2s_layout_id = self.env.ref('sbc_compassion.b2s_l6')

        # Check that layout L4 translation gets on second page
        if self.b2s_layout_id == self.env.ref('sbc_compassion.b2s_l4') and \
                not translate_text.startswith('#PAGE#'):
            translate_text = '#PAGE#' + translate_text
        self.write({
            target_text: translate_text.replace('\r', ''),
            'state': state,
            language_field: translate_lang_id,
            'translator_id': translator_partner.id})

        # Send to GMC
        if self.direction == 'Supporter To Beneficiary':
            self.create_commkit()
        else:
            # Recompose the letter image and process letter
            if super(Correspondence, self).process_letter():
                self.send_communication()

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
        src_lang_id = False
        dst_lang_id = False
        if self.direction == 'Supporter To Beneficiary':
            # Check that the letter is not yet sent to GMC
            if self.kit_identifier:
                raise UserError(_("Letter already sent to GMC cannot be "
                                  "translated! [%s]") % self.kit_identifier)

            src_lang_id = self.original_language_id
            child_langs = self.beneficiary_language_ids.filtered(
                'translatable')
            if child_langs:
                dst_lang_id = child_langs[-1]
            else:
                dst_lang_id = self.env.ref(
                    'child_compassion.lang_compassion_english')

        elif self.direction == 'Beneficiary To Supporter':
            if self.original_language_id and \
                    self.original_language_id.translatable:
                src_lang_id = self.original_language_id
            else:
                src_lang_id = self.env.ref(
                    'child_compassion.lang_compassion_english')
            dst_lang_id = self.supporter_languages_ids.filtered(
                lambda lang: lang.lang_id and lang.lang_id.code ==
                self.partner_id.lang)

        return src_lang_id, dst_lang_id

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
            file_ = BytesIO(base64.b64decode(self.letter_image))
            nas_share_name = self.env.ref(
                'sbc_switzerland.nas_share_name').value

            nas_letters_store_path = self.env.ref(
                'sbc_switzerland.nas_letters_store_path').value + file_name
            smb_conn.storeFile(nas_share_name,
                               nas_letters_store_path, file_)

            logger.info('File {} store on NAS with success'
                        .format(self.file_name))
        else:
            raise UserError(_('Connection to NAS failed'))

    # CRON Methods
    ##############
    @api.model
    def check_local_translation_done(self):
        reload(sys)
        sys.setdefaultencoding('UTF8')
        tc = translate_connector.TranslateConnect()
        letters_to_update = tc.get_translated_letters()

        for letter in letters_to_update:
            try:
                with api.Environment.manage():
                    with registry(
                            self.env.cr.dbname).cursor() as new_cr:
                        # Create a new environment with new cursor database
                        new_env = api.Environment(new_cr, self.env.uid,
                                                  self.env.context)
                        correspondence = self.with_env(new_env).browse(
                            letter["letter_odoo_id"])
                        logger.info(
                            ".....CHECK TRANSLATION FOR LETTER {}"
                            .format(correspondence.id)
                        )
                        correspondence.update_translation(
                            letter["target_lang"], letter["text"],
                            letter["translator"])
                        tc.update_translation_to_treated(letter["id"])
            except Exception as e:
                logger.error(
                    "Error fetching a translation on translation platform: {}"
                    .format(e.message)
                )
        return True
