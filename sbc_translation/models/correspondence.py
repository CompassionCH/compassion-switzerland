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
import tempfile

from . import translate_connector

from openerp import models, api
from openerp.tools.config import config

from smb.SMBConnection import SMBConnection
from openerp.tools.translate import _

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
        sponsorship = self.env['recurring.contract'].browse(
            vals['sponsorship_id'])

        letter_lang_id = vals['original_language_id']

        if letter_lang_id.translatable:
            letter = super(Correspondence, self.with_context(
                no_comm_kit=True)).create(vals)
            self.send_local_translate(letter, sponsorship)
        else:
            letter = super(SponsorshipCorrespondence, self).create(vals)

        return letter

    def send_local_translate(self, letter, sponsorship):
        # Insert the letter in the mysql data base
        tc = translate_connector.TranslateConnect()
        # Send letter to local translate platform
        text_id = tc.upsert_text(sponsorship, letter)
        translation_id = tc.upsert_translation(text_id, letter)
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
            with tempfile.NamedTemporaryFile(suffix='.pdf') as file_:
                file_.write(base64.b64decode(
                    letter.letter_image.with_context(
                        bin_size=False).datas))
                file_.flush()
                file_.seek(0)
                config_obj = self.env['ir.config_parameter']
                nas_share_name = (config_obj.search(
                    [('key', '=', 'sbc_translation.nas_share_name')])[0]).value

                child = sponsorship.child_id
                sponsor = sponsorship.partner_id
                letter_name = "_".join(
                    (child.code, sponsor.ref, str(letter.id)))
                letter_name = ".".join((letter_name, 'pdf'))

                nas_letters_store_path = (config_obj.search(
                    [('key', '=', 'sbc_translation.nas_letters_store_path')])
                    [0]).value + letter_name
                smb_conn.storeFile(nas_share_name,
                                   nas_letters_store_path, file_)

                logger.info('File {} store on NAS with success'
                            .format(letter.letter_image.name))

                ##############################################################
                #             DOESN'T WORK !!!                               #
                ##############################################################
                letter.state = 'Global Partner translation queue'
        else:
            raise Exception('Connection to NAS failed')

    # CRON Methods
    ##############
    @api.model
    def check_local_translation_done(self):
        tc = translate_connector.TranslateConnect()
        letters_to_update = tc.get_translated_letters()

        logger.info("CRON TASK check_local_translation_done CALL")

        if letters_to_update == -1:
            logger.info("NO SPONSORSHIP CORRESPPONDENCE LETTERS TO UPDATE")
        else:
            for letter in letters_to_update:
                sponsorship = self.browse(letter["letter_odoo_id"])
                reload(sys)
                sys.setdefaultencoding('UTF8')
                logger.info("sponshorship id : {}\ntraduction {}".
                            format(sponsorship.id, letter["text"]))
                tg_lang = letter["target_lang"]
                target_lang_id = self.env['res.lang.compassion'].search(
                    [('code_iso', '=', tg_lang)]).id
                # find the good text to writte
                if tg_lang == 'eng':
                    target_text = 'english_text'
                elif tg_lang in self.get_child_langs_code(sponsorship):
                    target_text = 'translated_text'
                else:
                    logger.error("Correspondence letters language no match")

                # UPDATE Odoo Database
                sponsorship.write(
                    {target_text: letter["text"],
                     'state': 'Received in the system',
                     'destination_language_id': target_lang_id})

                # Send to GMC
                action_id = self.env.ref('onramp_compassion.create_commkit').id
                self.env['gmc.message.pool'].create({
                    'action_id': action_id,
                    'object_id': letter["letter_odoo_id"]
                })

                tc.remove_letter(letter["id"])

    def get_child_langs_code(self, sponsorship):
        """ Return children's code iso """
        codes = []
        for lang_id in sponsorship.child_id.project_id.country_id.\
                spoken_lang_ids:
            codes.append(lang_id.code_iso)
        return codes
