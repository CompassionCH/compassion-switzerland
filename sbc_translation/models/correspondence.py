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
        """ Create a message for sending the CommKit only if the preferred
            language is the same as the letter's language else send the letter
            on the local translate plaforme.
            """
        sponsorship = self.env['recurring.contract'].browse(
            vals['sponsorship_id'])

        # Get languages
        letter_lang_id = vals['original_language_id']
        sponsor_lang_id = sponsorship.reading_language.id
        english_lang_id = self.env['res.lang.compassion']\
            .search([('name', '=', 'English')]).id
        child_lang_ids = sponsorship.child_id.project_id.country_id\
            .spoken_lang_ids.ids
        valid_lang = child_lang_ids + [english_lang_id, sponsor_lang_id]
        # if the letter's language is english, default correspondence language
        # or the child's country's languages the letter is directly sending to
        # GMC.
        if letter_lang_id in valid_lang:
            letter = super(Correspondence, self).create(vals)
        else:
            letter = super(Correspondence, self.with_context(
                no_comm_kit=True)).create(vals)
            self.send_local_translate(letter, sponsorship)
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
                letter.state = 'local translation on local platform'
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
                sponsorship_id = letter["letter_odoo_id"]
                reload(sys)
                sys.setdefaultencoding('UTF8')
                logger.info("sponshorship id : {}\ntraduction {}".
                            format(letter["letter_odoo_id"], letter["text"]))

                # UPDATE Odoo Database
                self.browse(sponsorship_id).write(
                    {'original_text': letter["text"], 'state':
                     'Received in the system'})

                # Send to GMC
                action_id = self.env.ref('onramp_compassion.create_commkit').id
                self.env['gmc.message.pool'].create({
                    'action_id': action_id,
                    'object_id': letter["letter_odoo_id"]
                })

                # REMOVE translation from local platform translation
                tc.remove_from_translation_status(letter["id"])
                text_id = tc.remove_from_translation(letter["id"])
                tc.remove_from_text(text_id)

    @api.model
    def get_s2b_states(self):
        logger.info('State Local Translation done')
        """ Supporter to Beneficiary states """
        states = super(SponsorshipCorrespondence, self).get_s2b_states()
        states.insert(1,
                      ('local translation on local platform',
                       _('Local Translation')))
        return states
