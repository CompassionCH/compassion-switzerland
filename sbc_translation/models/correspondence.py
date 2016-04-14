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

from io import BytesIO
from . import translate_connector

from openerp import models, api
from openerp.tools.config import config

from smb.SMBConnection import SMBConnection

import logging
logger = logging.getLogger(__name__)


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
             the local translate plaforme.
        """
        if vals.get('direction') == "Beneficiary To Supporter":
            correspondence = super(Correspondence, self).create(vals)
        else:
            sponsorship = self.env['recurring.contract'].browse(
                vals['sponsorship_id'])

            original_lang = self.env['res.lang.compassion'].browse(
                vals.get('original_language_id'))

            if original_lang.translatable and original_lang not in sponsorship\
                    .child_id.project_id.country_id.spoken_lang_ids:
                correspondence = super(Correspondence, self.with_context(
                    no_comm_kit=True)).create(vals)
                correspondence.send_local_translate()
            else:
                correspondence = super(Correspondence, self).create(vals)

        return correspondence

    def process_letter(self):
        """ Overloading method """
        super(Correspondence, self).process_letter()
        if self.destination_language_id not in self.supporter_languages_ids:
            self.send_local_translate()

    def send_local_translate(self):
        child = self.sponsorship_id.child_id

        # Specify the src and dst language
        src_lang_id = False
        dst_lang_id = False
        if self.direction == 'Supporter To Beneficiary':
            # Source language
            src_lang_id = self.original_language_id
            # Define the destination language
            child_langs = child.project_id.country_id.spoken_lang_ids
            translate_langs = self.env['res.lang.compassion']\
                .search([('translatable', '=', True)])
            dst_lang_id = (child_langs & translate_langs)[-1]
        elif self.direction == 'Beneficiary To Supporter':
            src_lang_id = self.destination_language_id
            dst_lang_id = self.sponsorship_id.reading_language
        else:
            raise Exception('Direction not define')

        # File name
        sponsor = self.sponsorship_id.partner_id
        file_name = "_".join(
            (child.code, sponsor.ref, str(self.id))) + '.pdf'

        # Send letter to local translate platform
        tc = translate_connector.TranslateConnect()
        text_id = tc.upsert_text(self, file_name,
                                 tc.get_lang_id(src_lang_id),
                                 tc.get_lang_id(dst_lang_id),
                                 )
        translation_id = tc.upsert_translation(text_id, self)
        tc.upsert_translation_status(translation_id)

        # Transfert file on the NAS

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

            self.state = 'Global Partner translation queue'
        else:
            raise Exception('Connection to NAS failed')

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
                                "Odoo DB. Remove it manually on MySQL DB.")
                               .format(correspondence.id))
                continue

            translate_lang = letter["target_lang"]
            translate_lang_id = self.env['res.lang.compassion'].search(
                [('code_iso', '=', translate_lang)]).id

            # Writte in the good text field
            if correspondence.direction == 'Supporter To Beneficiary':
                state = 'Received in the system'
                if translate_lang == 'eng':
                    target_text = 'english_text'
                elif translate_lang in correspondence.child_id.project_id\
                        .country_id.spoken_lang_ids.mapped('code_iso'):
                    target_text = 'translated_text'
                else:
                    raise AssertionError(
                        'letter {} was translated in a wrong language: {}'
                        .format(correspondence.id, translate_lang))
            else:
                state = 'Published to Global Partner'
                target_text = 'translated_text'

            # UPDATE Odoo Database
            correspondence.write(
                {target_text: letter["text"],
                 'state': state,
                 'destination_language_id': translate_lang_id})

            # Send to GMC
            if correspondence.direction == 'Supporter To Beneficiary':
                action_id = self.env.ref(
                    'onramp_compassion.create_commkit').id
                self.env['gmc.message.pool'].create({
                    'action_id': action_id,
                    'object_id': letter["letter_odoo_id"]
                })

            tc.remove_letter(letter["id"])
