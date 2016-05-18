# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Stephane Eicher <eicher31@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
import sys
import base64
import detectlanguage

from io import BytesIO
from openerp.exceptions import Warning

from . import translate_connector

from openerp import models, api, fields, _
from openerp.tools.config import config

from smb.SMBConnection import SMBConnection

import logging
logger = logging.getLogger(__name__)


class Correspondence(models.Model):
    """ This class intercepts a letter before it is sent to GMC.
        Letters are pushed to local translation platform if needed.
        """

    _inherit = 'correspondence'

    has_valid_language = fields.Boolean(compute='_compute_has_valid_language')

    ##########################################################################
    #                              ORM METHODS                               #
    ##########################################################################

    @api.model
    def create(self, vals):
        """ Create a message for sending the CommKit after be translated on
             the local translate plaforme.
        """
        if vals.get('direction') == "Beneficiary To Supporter":
            correspondence = super(Correspondence, self).create(vals)
        else:
            sponsorship = self.env['recurring.contract'].browse(
                vals['sponsorship_id'])

            original_lang = self.env['res.lang.compassion'].browse(
                vals.get('original_language_id'))

            if original_lang.translatable and original_lang not in \
                    sponsorship.child_id.project_id.country_id.spoken_lang_ids:
                correspondence = super(Correspondence, self.with_context(
                    no_comm_kit=True)).create(vals)
                correspondence.send_local_translate()
            else:
                correspondence = super(Correspondence, self).create(vals)

        return correspondence

    ##########################################################################
    #                             PUBLIC METHODS                             #
    ##########################################################################
    def process_letter(self):
        """ Called when B2S letter is Published. Check if translation is
         needed and upload to translation platform. """
        for letter in self:
            if letter.translation_language_id not in \
                    letter.supporter_languages_ids or \
                    not self.has_valid_language:
                letter.download_attach_letter_image()
                letter.send_local_translate()
            else:
                super(Correspondence, letter).process_letter()

    @api.one
    def _compute_has_valid_language(self):
        """ Detect if text is writed in the language corresponding to the
        language_id """
        self.has_valid_language = False
        if self.translated_text is not None and \
                self.translation_language_id is not None:
            s = self.translated_text.strip(' \t\n\r')
            if s != "":
                # find the language name of text argument
                detectlanguage.configuration.api_key = config.get(
                    'detect_language_api_key')
                languageName = ""
                langs = detectlanguage.languages()
                codeLang = detectlanguage.simple_detect(self.translated_text)
                for lang in langs:
                    if lang.get("code") == codeLang:
                        languageName = lang.get("name").lower()
                        break
                self.has_valid_language = languageName == \
                    self.translation_language_id.name.lower()

    @api.one
    def send_local_translate(self):
        """
        Sends the letter to the local translation platform.
        :return: None
        """
        child = self.sponsorship_id.child_id

        # Specify the src and dst language
        src_lang_id, dst_lang_id = self._get_translation_langs()

        # File name
        sponsor = self.sponsorship_id.partner_id
        file_name = "_".join(
            (child.unique_id, sponsor.ref, str(self.id))) + '.pdf'

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

    @api.one
    def remove_local_translate(self):
        """
        Remove a letter from local translation platform and change state of
        letter in Odoo
        :return: None
        """
        tc = translate_connector.TranslateConnect()
        tc.remove_translation_with_odoo_id(self.id)
        if self.direction == 'Supporter To Beneficiary':
            self.state = 'Received in the system'
        else:
            self.state = 'Published to Global Partner'

    @api.one
    def update_translation(self, translate_lang, translate_text, translator):
        """
        Puts the translated text into the correspondence.
        :param translate_lang: code_iso of the language of the translation
        :param translate_text: text of the translation
        :return: None
        """
        translate_lang_id = self.env['res.lang.compassion'].search(
            [('code_iso', '=', translate_lang)]).id
        translator_partner = self.env['res.partner'].search([
            ('ref', '=', translator)])

        if self.direction == 'Supporter To Beneficiary':
            state = 'Received in the system'

            # Write in the good text field
            if translate_lang == 'eng':
                target_text = 'english_text'
            elif translate_lang in self.child_id.project_id \
                    .country_id.spoken_lang_ids.mapped('code_iso'):
                # TODO After release R4 replace with 'translated_text'
                target_text = 'english_text'
            else:
                raise AssertionError(
                    'letter {} was translated in a wrong language: {}'
                    .format(self.id, translate_lang))
        else:
            state = 'Published to Global Partner'
            target_text = 'translated_text'

        # Check that layout L4 translation gets on second page
        if self.b2s_layout_id == self.env.ref('sbc_compassion.b2s_l4') and \
                not translate_text.startswith('#PAGE#'):
            translate_text = '#PAGE#' + translate_text
        self.write({
            target_text: translate_text.replace('\r', ''),
            'state': state,
            'translation_language_id': translate_lang_id,
            'translator_id': translator_partner.id})

        # Send to GMC
        if self.direction == 'Supporter To Beneficiary':
            # TODO Until R4 or bug with english_text is resolved
            self.write({
                'original_text': translate_text.replace('\r', ''),
            })
            action_id = self.env.ref(
                'onramp_compassion.create_commkit').id
            self.env['gmc.message.pool'].create({
                'action_id': action_id,
                'object_id': self.id
            })
        else:
            # Recompose the letter image and process letter
            self.letter_image.unlink()
            super(Correspondence, self).process_letter()

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
            - src_lang is the original language if translatable, else the
              current translated language of the letter (mostly english)
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
                raise Warning(_("Letter already sent to GMC cannot be "
                                "translated! [%s]") % self.kit_identifier)

            src_lang_id = self.original_language_id
            child_langs = self.beneficiary_language_ids.filtered(
                'translatable')
            if child_langs:
                dst_lang_id = child_langs[-1]
            else:
                dst_lang_id = self.env.ref(
                    'sbc_compassion.lang_compassion_english')

        elif self.direction == 'Beneficiary To Supporter':
            if self.original_language_id and \
                    self.original_language_id.translatable:
                src_lang_id = self.original_language_id
            else:
                src_lang_id = self.translation_language_id
            dst_lang_id = self.supporter_languages_ids.filtered(
                lambda lang: lang.lang_id and lang.lang_id.code ==
                self.correspondant_id.lang)

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
            file_ = BytesIO(base64.b64decode(
                self.letter_image.with_context(
                    bin_size=False).datas))
            nas_share_name = self.env.ref(
                'sbc_translation.nas_share_name').value

            nas_letters_store_path = self.env.ref(
                'sbc_translation.nas_letters_store_path').value + file_name
            smb_conn.storeFile(nas_share_name,
                               nas_letters_store_path, file_)

            logger.info('File {} store on NAS with success'
                        .format(self.letter_image.name))
        else:
            raise Warning(_('Connection to NAS failed'))

    # CRON Methods
    ##############
    @api.model
    def check_local_translation_done(self):
        reload(sys)
        sys.setdefaultencoding('UTF8')
        tc = translate_connector.TranslateConnect()
        letters_to_update = tc.get_translated_letters()

        for letter in letters_to_update:
            correspondence = self.browse(letter["letter_odoo_id"])
            if not correspondence.exists():
                logger.warning(("The correspondence id {} doesn't exist in the"
                                "Odoo DB. Remove it manually on MySQL DB. \
                                'todo_id' is set to 5 => 'Pas sur Odoo'")
                               .format(correspondence.id))
                tc.update_translation_to_not_in_odoo(letter["id"])
                continue

            correspondence.update_translation(letter["target_lang"],
                                              letter["text"],
                                              letter["translator"])
            # tc.remove_letter(letter["text_id"])
            # update: don't remove letter but set todo id to 'Traité'
            tc.update_translation_to_treated(letter["id"])
        return True
