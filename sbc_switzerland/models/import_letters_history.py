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
import base64
import logging
import time
import zipfile
from io import BytesIO

from odoo import fields, models, api, _, exceptions
from odoo.tools.config import config
from odoo.addons.sbc_compassion.tools import import_letter_functions as func
from . import translate_connector

logger = logging.getLogger(__name__)

try:
    import pysftp
    from smb.SMBConnection import SMBConnection
    from smb.smb_structs import OperationFailure
    from pyPdf import PdfFileWriter, PdfFileReader
    from pyPdf.pdf import PageObject
except ImportError:
    logger.warning("Please install python dependencies.")


class ImportLettersHistory(models.Model):
    """
    Keep history of imported letters.
    This class add to is parent the possibility to select letters to import
    from a specify config.
    The code is reading QR codes in order to detect child and partner codes
    for every letter, using the zxing library for code detection.
    """
    _name = 'import.letters.history'
    _inherit = ['import.letters.history', 'import.letter.config']

    manual_import = fields.Boolean(
        string=_("Manual import"),
        default=False)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.onchange("data", "import_folder_path")
    def _count_nber_letters(self):
        """
        Counts the number of scans. If a zip file is given, the number of
        scans inside is counted.
        """
        if self.manual_import or (
                self.state and self.state != 'draft'):
            super(ImportLettersHistory, self)._count_nber_letters()
        else:
            # files are not selected by user so we find them on NAS
            # folder 'Imports' counter
            tmp = 0

            smb_conn = self._get_smb_connection()
            share_nas = self.env.ref('sbc_switzerland.share_on_nas').value
            imported_letter_path = self.import_folder_path

            if smb_conn and smb_conn.connect(
                SmbConfig.smb_ip, SmbConfig.smb_port) and \
                    imported_letter_path:
                imported_letter_path = self.check_path(imported_letter_path)

                try:
                    listPaths = smb_conn.listPath(
                        share_nas,
                        imported_letter_path)
                except OperationFailure:
                    logger.info('--------------- PATH NO CORRECT -----------')
                    listPaths = []

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
                        try:
                            zip_ = zipfile.ZipFile(file_obj, 'r')
                            list_file = zip_.namelist()
                            # loop over all files in zip
                            for tmp_file in list_file:
                                tmp += (func.check_file(
                                    tmp_file) == 1)
                        except zipfile.BadZipfile:
                            raise exceptions.UserError(
                                _('Zip file corrupted (' +
                                  sharedFile.filename + ')'))
                        except zipfile.LargeZipFile:
                            raise exceptions.UserError(
                                _('Zip64 is not supported(' +
                                  sharedFile.filename + ')'))
                smb_conn.close()
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
        Analyze the imports in order to create the letter's lines
        """
        if not self.manual_import:
            # when letters are in a folder on NAS redefine method
            for letters_import in self:
                letters_import.state = 'pending'
                if self.env.context.get('async_mode', True):
                    letters_import.with_delay()._run_analyze()
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

    @api.multi
    def button_save(self):
        """
        When saving the import_line as correspondences, move pdf file in the
        done folder on the NAS and remove image attachment (Web letter case)
        """
        try:
            for import_letters in self:
                if import_letters.config_id.name == \
                        self.env.ref('sbc_switzerland.web_letter').name:
                    for line in import_letters.import_line_ids:
                        # build part of filename, corresponding to this web
                        # import
                        # letters remove part after '-' caracter (including)
                        # corresponding to the page number
                        part_filename = (line.letter_image.name[:-4]).split(
                            '-')[0]

                        share_nas = self.env.ref(
                            'sbc_switzerland.share_on_nas').value

                        smb_conn = self._get_smb_connection()
                        if smb_conn and smb_conn.connect(
                                SmbConfig.smb_ip, SmbConfig.smb_port):
                            imported_letter_path = self.env.ref(
                                'sbc_switzerland.scan_letter_imported').value
                            listPaths = smb_conn.listPath(
                                share_nas,
                                imported_letter_path)

                            # loop in import folder and find pdf corresponding
                            # to this web letter and eventual attached image
                            image_ext = None
                            file_to_save = False
                            for sharedFile in listPaths:
                                ext = sharedFile.filename[-4:]
                                if part_filename == sharedFile.filename[:-4]:
                                    if ext == '.pdf':
                                        file_to_save = True
                                    else:
                                        image_ext = ext

                            # move web letter on 'Done' folder on the NAS
                            if file_to_save:
                                filename = part_filename + '.pdf'
                                file_obj = BytesIO()
                                smb_conn.retrieveFile(
                                    share_nas, imported_letter_path + filename,
                                    file_obj)
                                file_obj.seek(0)
                                self._copy_imported_to_done_letter(
                                    filename, file_obj, False)
                                # delete files corresponding to web letter in
                                # 'Import'
                                try:
                                    smb_conn.deleteFiles(
                                        share_nas,
                                        imported_letter_path + filename)
                                except Exception as inst:
                                    logger.info(
                                        'Failed to delete pdf web letter'
                                        .format(inst))

                                # image is attached to this letter so we
                                # remove it
                                if image_ext:
                                    try:
                                        smb_conn.deleteFiles(
                                            share_nas,
                                            imported_letter_path +
                                            part_filename + image_ext)
                                    except Exception as inst:
                                        logger.info(
                                            'Failed to delete attached '
                                            'image {}'.format(inst))

                if import_letters.manual_import:
                    self._manage_all_imported_files()

            super(ImportLettersHistory, self).button_save()

        except Exception as e:
            logger.info("Exception during letter import: {}", e)
            # bug during import, so we remove letter sent on translation
            # platform
            for letters in self:
                for corresp in letters.letters_ids:
                    if corresp.state == "Global Partner translation queue":
                        logger.info("LETTER DELETE FROM TRANSLATION PLATFORM")
                        tc = translate_connector.TranslateConnect()
                        tc.remove_translation_with_odoo_id(corresp.id)
            raise e

        return True

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

        share_nas = self.env.ref('sbc_switzerland.share_on_nas').value

        smb_conn = self._get_smb_connection()

        if not self.manual_import:
            imported_letter_path = self.check_path(self.import_folder_path)
            if smb_conn and smb_conn.connect(
                    SmbConfig.smb_ip, SmbConfig.smb_port):
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

                            self._analyze_attachment(zip_.read(f), f)
                            progress += 1
                smb_conn.close()
            else:
                logger.info('Failed to list files in Imports on the NAS in \
                emplacement: {}'.format(
                    imported_letter_path))
        else:
            super(ImportLettersHistory, self)._run_analyze()

        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()
        if not self.manual_import:
            self._manage_all_imported_files()
        self.import_completed = True
        logger.info("Imported letters analysis completed.")

    def _save_imported_letter(self, attachment):
        """
        Save attachment letter to a shared folder on the NAS ('Imports')
            - attachment : the attachment to save
        Done by Michael Sandoz 02.2016
        """
        # Store letter on a shared folder on the NAS:
        # Copy file in the imported letter folder
        smb_conn = self._get_smb_connection()
        if smb_conn and smb_conn.connect(SmbConfig.smb_ip, SmbConfig.smb_port):
            logger.info("Try to save file {} !".format(attachment.name))

            file_ = BytesIO(base64.b64decode(
                            attachment.with_context(bin_size=False).datas))

            share_nas = self.env.ref('sbc_switzerland.share_on_nas').value

            if self.manual_import:
                imported_letter_path = self.env.ref(
                    'sbc_switzerland.scan_letter_imported'
                ).value + attachment.name
            else:
                imported_letter_path = self.check_path(
                    self.import_folder_path) + attachment.name

            smb_conn.storeFile(share_nas, imported_letter_path, file_)
            smb_conn.close()
        return True

    def _manage_all_imported_files(self):
        """
        File management at the end of correct import:
            - Save files in their final location on the NAS
            - Delete files from their import location on the NAS
        Done by Michael Sandoz 02.2016
        """
        share_nas = self.env.ref('sbc_switzerland.share_on_nas').value
        # to delete after treatment
        list_zip_to_delete = []
        imported_letter_path = ""
        if self.manual_import:
            imported_letter_path = self.env.ref(
                'sbc_switzerland.scan_letter_imported').value
        else:
            imported_letter_path = self.check_path(self.import_folder_path)

        smb_conn = self._get_smb_connection()
        if smb_conn and smb_conn.connect(
                SmbConfig.smb_ip, SmbConfig.smb_port):

            listPaths = smb_conn.listPath(share_nas, imported_letter_path)
            for sharedFile in listPaths:
                if func.check_file(sharedFile.filename) == 1:
                    # when this is manual import we don't have to copy all
                    # files, web letters are stock in the same folder...
                    if not self.manual_import or self.is_in_list_letter(
                            sharedFile.filename):
                        file_obj = BytesIO()
                        smb_conn.retrieveFile(
                            share_nas,
                            imported_letter_path +
                            sharedFile.filename,
                            file_obj)
                        file_obj.seek(0)
                        self._copy_imported_to_done_letter(
                            sharedFile.filename, file_obj, True)
                elif func.isZIP(sharedFile.filename):
                    zip_file = BytesIO()

                    smb_conn.retrieveFile(
                        share_nas,
                        imported_letter_path +
                        sharedFile.filename,
                        zip_file)
                    zip_file.seek(0)
                    zip_ = zipfile.ZipFile(
                        zip_file, 'r')

                    zip_to_remove = False
                    for f in zip_.namelist():
                        # when this is manual import we are not sure that this
                        # zip contains current letters treated
                        if not self.manual_import or self.is_in_list_letter(f):
                            self._copy_imported_to_done_letter(
                                f, BytesIO(zip_.read(f)), False)
                            zip_to_remove = True

                    if zip_to_remove:
                        list_zip_to_delete.append(sharedFile.filename)

            # delete zip file from origin import folder on the NAS
            for filename in list_zip_to_delete:
                try:
                    smb_conn.deleteFiles(
                        share_nas,
                        imported_letter_path +
                        filename)
                except Exception as inst:
                    logger.info('Failed to delete zip file on NAS: {}'
                                .format(inst))
            smb_conn.close()

    def is_in_list_letter(self, filename):
        """
        Check if given filename is in import letter list
        """
        for line in self.import_line_ids:
            if filename[:-4] in line.letter_image.name:
                return True
        return False

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
        smb_conn = self._get_smb_connection()
        if smb_conn and smb_conn.connect(SmbConfig.smb_ip, SmbConfig.smb_port):
            logger.info("Try to copy file {} !".format(filename))

            # Copy file in attachment in the done letter folder
            share_nas = self.env.ref('sbc_switzerland.share_on_nas').value

            # Add end path corresponding to the end of the import folder path
            end_path = ""
            if self.import_folder_path:
                end_path = self.check_path(self.import_folder_path)
                end_path = end_path.split("\\")[-2] + "\\"
            done_letter_path = self.env.ref(
                'sbc_switzerland.scan_letter_done').value + end_path + filename

            smb_conn.storeFile(share_nas, done_letter_path, file_to_copy)

            # Delete file in the imported letter folder
            if deleteFile:
                imported_letter_path = ""
                if self.manual_import:
                    imported_letter_path = self.env.ref(
                        'sbc_switzerland.scan_letter_imported'
                    ).value + filename
                else:
                    imported_letter_path = self.check_path(
                        self.import_folder_path) + filename

                try:
                    smb_conn.deleteFiles(share_nas, imported_letter_path)
                except Exception as inst:
                    logger.info('Failed to delete a file on NAS : {}'.
                                format(inst))

            smb_conn.close()
        return True

    def check_path(self, path):
        """" Add backslash at end of path if not contains ever one """
        if path and not path[-1] == '\\':
            path = path + "\\"
        return path

    def _get_smb_connection(self):
        """" Retrieve configuration SMB """
        if not (SmbConfig.smb_user and SmbConfig.smb_pass and
                SmbConfig.smb_ip and SmbConfig.smb_port):
            return False
        else:
            return SMBConnection(
                SmbConfig.smb_user, SmbConfig.smb_pass, 'openerp', 'nas')

    @api.model
    def import_web_letter(self, child_code, sponsor_ref,
                          original_text, template_name, pdf_filename,
                          attachment_filename, ext):
        """
        Call when a letter is set on web site:
            - add web letter to an import set with import letter config
              'Web letter'
        """
        try:
            # Find existing config or create a new one
            web_letter_id = self.env.ref('sbc_switzerland.web_letter').id
            import_config = self.search([
                ('config_id', '=', web_letter_id),
                ('state', '!=', 'done')], limit=1)
            if not import_config:
                import_config = self.create({
                    'config_id': web_letter_id, 'state': 'open'})

            # Find child
            if child_code:
                # Retrieve child code and find corresponding id
                child_field = 'local_id'
                if len(child_code) == 9:
                    child_field = 'code'
                model_child = self.env['compassion.child'].search(
                    [(child_field, '=', child_code), ('state', '=', 'P')])

                child_id = model_child.id

            if sponsor_ref:
                # Retrieve sponsor reference and find corresponding id
                model_sponsor = self.env['res.partner'].search(
                    ['|', ('ref', '=', sponsor_ref),
                     ('global_id', '=', sponsor_ref),
                     ('has_sponsorships', '=', True)])
                sponsor_id = model_sponsor.id

            # Check if a sponsorship exists
            self.env['recurring.contract'].search([
                ('child_id', '=', child_id),
                ('correspondant_id', '=', sponsor_id),
                ('is_active', '=', True)], limit=1).ensure_one()

            lang = self.env['correspondence'].detect_lang(original_text)
            lang_id = None
            if lang:
                lang_id = lang.id

            template = None
            if template_name:
                # Retrieve template name and find corresponding id
                template = self.env['correspondence.template'].search(
                    [('name', '=', template_name)], limit=1)

            # save_letter pdf
            sftp_host = config.get('wp_sftp_host')
            sftp_user = config.get('wp_sftp_user')
            sftp_pw = config.get('wp_sftp_pwd')
            sftp = pysftp.Connection(sftp_host, sftp_user, password=sftp_pw)
            pdf_data = sftp.open(pdf_filename).read()
            filename = 'WEB_' + sponsor_ref + '_' + \
                child_code + '_' + str(time.time())[:10] + '.pdf'

            pdf_letter = self.analyze_webletter(pdf_data)

            # analyze attachment to check template and create image preview
            line_vals, document_vals = func.analyze_attachment(
                self.env, pdf_letter, filename,
                template)

            for i in xrange(0, len(line_vals)):
                line_vals[i].update({
                    'import_id': import_config.id,
                    'partner_id': sponsor_id,
                    'child_id': child_id,
                    'letter_language_id': lang_id,
                    'original_text': original_text,
                    'source': 'website'
                })
                letters_line = self.env[
                    'import.letter.line'].create(line_vals[i])
                document_vals[i].update({
                    'res_id': letters_line.id,
                    'res_model': 'import.letter.line'
                })
                letters_line.letter_image = self.env[
                    'ir.attachment'].create(document_vals[i])

            import_config.import_completed = True

            logger.info("Try to copy file {} !".format(filename))
            # Copy file in attachment in the done letter folder
            share_nas = self.env.ref('sbc_switzerland.share_on_nas').value
            import_letter_path = self.env.ref(
                'sbc_switzerland.scan_letter_imported').value + filename

            file_pdf = BytesIO(pdf_letter)
            smb_conn = self._get_smb_connection()
            if smb_conn and smb_conn.connect(
                    SmbConfig.smb_ip, SmbConfig.smb_port):
                smb_conn.storeFile(share_nas, import_letter_path, file_pdf)

                # save eventual attachment
                if attachment_filename:
                    attachment_data = sftp.open(attachment_filename).read()
                    filename_attachment = filename.replace(".pdf", "." + ext)
                    logger.info("Try save attachment {} !"
                                .format(filename_attachment))

                    import_letter_path = self.env.ref(
                        'sbc_switzerland.scan_letter_imported').value + \
                        filename_attachment

                    file_attachment = BytesIO(attachment_data)
                    smb_conn.storeFile(
                        share_nas,
                        import_letter_path,
                        file_attachment)
                smb_conn.close()
            sftp.close()
            return True
        except:
            return False

    def analyze_webletter(self, pdf_letter):
        """
        Look if the web letter has a minimum of 2 page.
        If not add one blank page.
        """
        pdf = PdfFileReader(BytesIO(pdf_letter))

        if pdf.numPages < 2:
            final_pdf = PdfFileWriter()
            final_pdf.addPage(pdf.getPage(0))

            width = float(pdf.getPage(0).mediaBox.getWidth())
            height = float(pdf.getPage(0).mediaBox.getHeight())

            new_page = PageObject.createBlankPage(None, width, height)
            final_pdf.addPage(new_page)

            output_stream = BytesIO()
            final_pdf.write(output_stream)
            output_stream.seek(0)
            pdf_letter = output_stream.read()
            output_stream.close()
        return pdf_letter


class SmbConfig():
    """" Little class who contains SMB configuration """
    smb_user = config.get('smb_user')
    smb_pass = config.get('smb_pwd')
    smb_ip = config.get('smb_ip')
    smb_port = int(config.get('smb_port', 0))
