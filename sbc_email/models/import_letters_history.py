# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier, Loic Hausammann <loic_hausammann@hotmail.com>
#
#    The licence is in the file __openerp__.py
#
##############################################################################
"""
This module reads a zip file containing scans of mail and finds the relation
between the database and the mail.
"""
import logging
import base64
import zipfile

from openerp.addons.sbc_compassion.tools import import_letter_functions as func
from openerp import fields, models, api, _, exceptions

from io import BytesIO
from openerp.tools.config import config
from smb.SMBConnection import SMBConnection

from openerp.addons.connector.session import ConnectorSession
from openerp.addons.sbc_compassion.models import import_letters_history as ilh

logger = logging.getLogger(__name__)


class ImportLettersHistory(models.Model):
    """
    Keep history of imported letters.
    This class allows the user to import some letters (individually or in a
    zip file) in the database by doing an automatic analysis.
    The code is reading QR codes in order to detect child and partner codes
    for every letter, using the zxing library for code detection.
    """
    _inherit = "import.letters.history"

    from_imports_nas_folder = fields.Boolean(
        string="Import all content from NAS Imports folder",
        default=True)
    
    @api.model
    def create(self, vals):
        smb_user = config.get('smb_user')
        smb_pass = config.get('smb_pwd')
        smb_ip = config.get('smb_ip')
        smb_port = int(config.get('smb_port', 0))
        if not (smb_user and smb_pass and smb_ip and smb_port):
            return None
        
        return super(ImportLettersHistory, self).create(vals)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.multi
    @api.onchange(
        "data", "import_line_ids", "letters_ids", "from_imports_nas_folder")
    def _count_nber_letters(self):
        """
        Counts the number of scans. If a zip file is given, the number of
        scans inside is counted.
        """
        self.ensure_one()

        if not self.from_imports_nas_folder or (
                self.state and self.state != 'draft'):
            super(ImportLettersHistory, self)._count_nber_letters()
        else:
            # files are not selected by user so we find them on NAS
            # folder 'Imports'
            # counter
            tmp = 0
            # Retrieve configuration
#             smb_user = config.get('smb_user')
#             smb_pass = config.get('smb_pwd')
#             smb_ip = config.get('smb_ip')
#             smb_port = int(config.get('smb_port', 0))
#             if not (smb_user and smb_pass and smb_ip and smb_port):
#                 return False

            smb_conn = SMBConnection(
                smb_user,
                smb_pass,
                'openerp',
                'nas')
#             config_obj = self.env['ir.config_parameter']
#             share_nas = (config_obj.search(
#                 [('key', '=', 'sbc_compassion.share_on_nas')])
#                 [0]).value
#             imported_letter_path = (config_obj.search(
#                 [('key', '=', 'sbc_compassion.scan_letter_imported'
#                   )])[0]).value
            share_nas = self.env.ref('sbc_compassion.share_on_nas').value
            imported_letter_path = self.env.ref(
                'sbc_compassion.scan_letter_imported').value
            if smb_conn.connect(smb_ip, smb_port):
                listPaths = smb_conn.listPath(
                    share_nas,
                    imported_letter_path)
                for sharedFile in listPaths:
                    if func.check_file(sharedFile.filename) == 1:
                        tmp += 1
                    elif func.isZIP(sharedFile.filename):
                        logger.info(
                            'File to retrieve: {}'.format(
                                imported_letter_path +
                                sharedFile.filename))

                        file_obj = BytesIO()
                        smb_conn.retrieveFile(
                            share_nas,
                            imported_letter_path +
                            sharedFile.filename,
                            file_obj)
                        smb_conn.close()
                        try:
                            zip_ = zipfile.ZipFile(file_obj, 'r')
                            list_file = zip_.namelist()
                            # loop over all files in zip
                            for tmp_file in list_file:
                                tmp += (func.check_file(
                                    tmp_file) == 1)
                        except zipfile.BadZipfile:
                            raise exceptions.Warning(
                                _('Zip file corrupted (' +
                                  sharedFile.filename + ')'))
                        except zipfile.LargeZipFile:
                            raise exceptions.Warning(
                                _('Zip64 is not supported(' +
                                  sharedFile.filename + ')'))

            else:
                logger.info("""Failed to list files in imported \
                folder Imports oh the NAS in emplacement: {}""".format(
                    imported_letter_path))

            self.nber_letters = tmp

    ##########################################################################
    #                             VIEW CALLBACKS                             #
    ##########################################################################
    @api.multi
    def button_import(self):
        """
        Analyze the attachment in order to create the letter's lines
        """
        if self.from_imports_nas_folder:
            # when letters are in a folder on NAS redefine method
            for letters_import in self:
                letters_import.state = 'pending'
                if self.env.context.get('async_mode', True):
                    session = ConnectorSession.from_env(self.env)
                    ilh.import_letters_job.delay(
                        session, self._name, letters_import.id)
                else:
                    letters_import._run_analyze()
            return True
        else:
            # when letters selected by user, save them on NAS and call
            # super method
            for letters_import in self:
                if letters_import.data and self.env.context.get(
                        'async_mode', True):
                    for attachment in letters_import.data:
                        self._save_imported_letter(attachment)

            return super(ImportLettersHistory, self).button_import()

    #########################################################################
    #                             PRIVATE METHODS                           #
    #########################################################################
    def _run_analyze(self):
        """
        Analyze each attachment:
        - check for duplicate file names and skip them
        - decompress zip file if necessary
        - call _analyze_attachment for every resulting file
        """
        self.ensure_one()
        # keep track of file names to detect duplicates
        # file_name_history = []
        logger.info("Imported letters analysis started...")
        progress = 1

        # Added by Michael Sandoz begin
        # Case where letters are in 'Imports' folder on the NAS
#         config_obj = self.env['ir.config_parameter']
#         share_nas = (config_obj.search(
#             [('key', '=', 'sbc_compassion.share_on_nas')])[0]).value
#         imported_letter_path = (config_obj.search(
#             [('key', '=', 'sbc_compassion.scan_letter_imported')])[0]).value
        share_nas = self.env.ref('sbc_compassion.share_on_nas').value
        imported_letter_path = self.env.ref(
            'sbc_compassion.scan_letter_imported').value

        # Retrieve SMB configuration
#         smb_user = config.get('smb_user')
#         smb_pass = config.get('smb_pwd')
#         smb_ip = config.get('smb_ip')
#         smb_port = int(config.get('smb_port', 0))
#         if not (smb_user and smb_pass and smb_ip and smb_port):
#             return False
        smb_conn = SMBConnection(smb_user, smb_pass, 'openerp', 'nas')

        if self.from_imports_nas_folder:
            if smb_conn.connect(smb_ip, smb_port):
                listPaths = smb_conn.listPath(share_nas, imported_letter_path)
                for sharedFile in listPaths:
                    if func.check_file(sharedFile.filename) == 1:
                        logger.info("Analyzing letter {}/{}".format(
                            progress, self.nber_letters))

                        file_obj = BytesIO()
                        smb_conn.retrieveFile(
                            share_nas,
                            imported_letter_path +
                            sharedFile.filename,
                            file_obj)
                        file_obj.seek(0)
                        self._analyze_attachment(
                            file_obj.read(),
                            sharedFile.filename)
                        # saved imported letter to a share location NAS
                        # folder
#                         file_obj.seek(0)
#                         self._copy_imported_to_done_letter(
#                             sharedFile.filename,
#                             file_obj,
#                             True)

                        progress += 1
                    elif func.isZIP(sharedFile.filename):

                        zip_file = BytesIO()
                        # retrieve zip file from imports letters stored on
                        # NAS
                        smb_conn.retrieveFile(
                            share_nas,
                            imported_letter_path +
                            sharedFile.filename,
                            zip_file)
                        zip_file.seek(0)
                        zip_ = zipfile.ZipFile(
                            zip_file, 'r')
                        # loop over files inside zip
                        for f in zip_.namelist():
                            logger.info(
                                "Analyzing letter {}/{}".format(
                                    progress, self.nber_letters))

                            self._analyze_attachment(zip_.read(f), f, True)
#                             file_to_copy = BytesIO(zip_.read(f))
#                             self._copy_imported_to_done_letter(
#                                 f, file_to_copy, False)
                            progress += 1
                        # delete zip file on 'Imports' folder on the NAS
                        try:
                            smb_conn.deleteFiles(
                                share_nas,
                                imported_letter_path +
                                sharedFile.filename)
                        except Exception as inst:
                            logger.info('Failed to delete zip file on NAS: {}'
                                        .format(inst))
                smb_conn.close()
            else:
                logger.info('Failed to list files in Imports on the NAS in \
                emplacement: {}'.format(
                    imported_letter_path))
        else:
            super(ImportLettersHistory, self)._run_analyze()
            # if NAS contains zip file on Imports folder, delete them
            for attachment in self.data:
                if func.check_file(attachment.name) == 2:
                    try:
                        if smb_conn.connect(smb_ip, smb_port):
                            smb_conn.deleteFiles(
                                share_nas,
                                imported_letter_path +
                                attachment.name)
                    except Exception as inst:
                        logger.info('Failed to delete zip file \
                        on NAS: {}'.format(inst))
            # case where letters are selected by user
#             for attachment in self.data:
#                 if attachment.name not in file_name_history:
#                     file_name_history.append(attachment.name)
#                     file_data = base64.b64decode(attachment.with_context(
#                         bin_size=False).datas)
#                     # check for zip
#                     if func.check_file(attachment.name) == 2:
#                         zip_file = BytesIO(file_data)
#                         zip_ = zipfile.ZipFile(zip_file, 'r')
#                         for f in zip_.namelist():
#                             logger.info(
#                                 "Analyzing letter {}/{}".format(
#                                     progress, self.nber_letters))
#                             self._analyze_attachment(zip_.read(f), f,
#                                                      attachment.name)
# #
# #                             # saved imported letter to a shared NAS folder
# #                             file_to_copy = BytesIO(zip_.read(f))
# #                             self._copy_imported_to_done_letter(
# #                                 f, file_to_copy, False)
#                             progress += 1
#
#                         try:
#                             if smb_conn.connect(smb_ip, smb_port):
#                                 smb_conn.deleteFiles(
#                                     share_nas,
#                                     imported_letter_path +
#                                     attachment.name)
#                         except Exception as inst:
#                             logger.info('Failed to delete zip file \
#                             on NAS: {}'.format(inst))
#                     # case with normal format (PDF,TIFF)
#                     elif func.check_file(attachment.name) == 1:
#                         logger.info("Analyzing letter {}/{}".format(
#                             progress, self.nber_letters))
#                         self._analyze_attachment(file_data, attachment.name)
# #
# #                         file_to_copy = BytesIO(file_data)
# #                         self._copy_imported_to_done_letter(
# #                             attachment.name,
# #                             file_to_copy,
# #                             True)
#                         progress += 1
#                     else:
#                         raise exceptions.Warning(
#                             'Only zip/pdf/tiff files are supported.')
#                 else:
#                     raise exceptions.Warning(_('Two files are the same'))

        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()
        self.import_completed = True
        logger.info("Imported letters analysis completed.")

    def _analyze_attachment(self, file_data, file_name, is_zipfile=False):
        super(ImportLettersHistory, self)._analyze_attachment(
            file_data, file_name, is_zipfile)

        # save imported letter to a shared NAS folder
        file_to_copy = BytesIO(file_data)
        self._copy_imported_to_done_letter(
            file_name,
            file_to_copy,
            not is_zipfile)

    def _save_imported_letter(self, attachment):
        """
        Save attachment letter to a shared folder on the NAS ('Imports')
            - attachment : the attachment to save
        Done by Michael Sandoz 02.2016
        """
        """ Store letter on a shared folder on the NAS: """
        # Retrieve configuration
#         smb_user = config.get('smb_user')
#         smb_pass = config.get('smb_pwd')
#         smb_ip = config.get('smb_ip')
#         smb_port = int(config.get('smb_port', 0))
#         if not (smb_user and smb_pass and smb_ip and smb_port):
#             return False

        # Copy file in the imported letter folder
        smb_conn = SMBConnection(smb_user, smb_pass, 'openerp', 'nas')
        if smb_conn.connect(smb_ip, smb_port):
            logger.info("Try to save file {} !".format(attachment.name))
#             ext = os.path.splitext(attachment.name)[1]

            file_ = BytesIO(base64.b64decode(
                            attachment.with_context(bin_size=False).datas))

#             config_obj = self.env['ir.config_parameter']
#             share_nas = (config_obj.search(
#                 [('key', '=', 'sbc_compassion.share_on_nas')])[0]).value
#             imported_letter_path = (config_obj.search(
#                 [('key', '=', 'sbc_compassion.scan_letter_imported')])
#                 [0]).value + attachment.name
            share_nas = self.env.ref('sbc_compassion.share_on_nas').value
            imported_letter_path = self.env.ref(
                'scan_letter_imported').value + attachment.name
            smb_conn.storeFile(share_nas, imported_letter_path, file_)
            smb_conn.close()
        return True

    def _copy_imported_to_done_letter(
            self, filename, file_to_copy, deleteFile):
        """
        Copy letter from 'imported' folder to 'done' folder on  a shared folder
        on NAS
            - filename: filename to give to saved file
            - file_to_copy: the file to copy
            - deleteFile: set to true if file_to_copy must be deleted after the
              copy
        Done by Michael Sandoz 02.2016
        """
        # Retrieve configuration
#         smb_user = config.get('smb_user')
#         smb_pass = config.get('smb_pwd')
#         smb_ip = config.get('smb_ip')
#         smb_port = int(config.get('smb_port', 0))
#         if not (smb_user and smb_pass and smb_ip and smb_port):
#             return False

        smb_conn = SMBConnection(smb_user, smb_pass, 'openerp', 'nas')
        if smb_conn.connect(smb_ip, smb_port):
            logger.info("Try to copy file {} !".format(filename))

            # Copy file in attachment in the done letter folder
#             config_obj = self.env['ir.config_parameter']
#             share_nas = (config_obj.search(
#                 [('key', '=', 'sbc_compassion.share_on_nas')])[0]).value
#             imported_letter_path = (config_obj.search(
#                 [('key', '=', 'sbc_compassion.scan_letter_imported')])
#                 [0]).value + filename
#
#             done_letter_path = (config_obj.search(
#                 [('key', '=', 'sbc_compassion.scan_letter_done')])
#                 [0]).value + filename
            share_nas = self.env.ref('sbc_compassion.share_on_nas').value
            imported_letter_path = self.env.ref(
                'scan_letter_imported').value + filename
            done_letter_path = self.env.ref(
                'sbc_compassion.scan_letter_done').value + filename

            smb_conn.storeFile(share_nas, done_letter_path, file_to_copy)

            # Delete file in the imported letter folder
            if deleteFile:
                try:
                    smb_conn.deleteFiles(share_nas, imported_letter_path)
                except Exception as inst:
                    logger.info('Failed to delete a file on NAS : {}'.
                                format(inst))

            smb_conn.close()
        return True
