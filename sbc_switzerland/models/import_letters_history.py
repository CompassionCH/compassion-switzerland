##############################################################################
#
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emmanuel Mathier, Loic Hausammann <loic_hausammann@hotmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
"""
This module reads a zip file containing scans of mail and finds the relation
between the database and the mail.
"""
import base64
import logging
import subprocess
import zipfile
from io import BytesIO
from tempfile import NamedTemporaryFile

from odoo import fields, models, api, _, exceptions
from odoo.tools.config import config
from odoo.tools.misc import find_in_path
from odoo.addons.sbc_compassion.tools import import_letter_functions as func
from odoo.addons.queue_job.job import job, related_action
from . import translate_connector

logger = logging.getLogger(__name__)

try:
    from smb.SMBConnection import SMBConnection
    from smb.smb_structs import OperationFailure
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PyPDF2.pdf import PageObject
except ImportError:
    logger.warning("Please install python dependencies.")


class ImportLettersHistory(models.Model):
    """
    Keep history of imported letters.
    This class add to its parent the possibility to select letters to import
    from a specific config.
    The code is reading QR codes in order to detect child and partner codes
    for every letter, using the zxing library for code detection.
    """

    _inherit = "import.letters.history"

    manual_import = fields.Boolean("Manual import", default=False)

    ##########################################################################
    #                             FIELDS METHODS                             #
    ##########################################################################
    @api.onchange("data", "import_folder_path")
    def _compute_nber_letters(self):
        """
        Counts the number of scans. If a zip file is given, the number of
        scans inside is counted.
        """
        for letter in self:
            if letter.manual_import or (letter.state and letter.state != "draft"):
                super(ImportLettersHistory, letter)._compute_nber_letters()
            else:
                # files are not selected by user so we find them on NAS
                # folder 'Imports' counter
                tmp = 0

                smb_conn = letter._get_smb_connection()
                share_nas = letter.env.ref("sbc_switzerland.share_on_nas").value
                imported_letter_path = letter.import_folder_path

                if (
                        smb_conn
                        and smb_conn.connect(SmbConfig.smb_ip, SmbConfig.smb_port)
                        and imported_letter_path
                ):
                    imported_letter_path = letter.check_path(imported_letter_path)

                    try:
                        list_paths = smb_conn.listPath(share_nas, imported_letter_path)
                    except OperationFailure:
                        logger.error("--------------- PATH NOT CORRECT ---------------")
                        list_paths = []

                    for shared_file in list_paths:
                        if func.check_file(shared_file.filename) == 1:
                            tmp += 1
                        elif func.is_zip(shared_file.filename):
                            logger.debug(
                                "File to retrieve:"
                                f" {imported_letter_path + shared_file.filename}"
                            )

                            file_obj = BytesIO()
                            smb_conn.retrieveFile(
                                share_nas,
                                imported_letter_path + shared_file.filename,
                                file_obj,
                            )
                            try:
                                zip_ = zipfile.ZipFile(file_obj, "r")
                                list_file = zip_.namelist()
                                # loop over all files in zip
                                for tmp_file in list_file:
                                    tmp += func.check_file(tmp_file) == 1
                            except zipfile.BadZipfile:
                                raise exceptions.UserError(
                                    _(
                                        "Zip file corrupted ("
                                        + shared_file.filename
                                        + ")"
                                    )
                                )
                            except zipfile.LargeZipFile:
                                raise exceptions.UserError(
                                    _(
                                        "Zip64 is not supported("
                                        + shared_file.filename
                                        + ")"
                                    )
                                )
                    smb_conn.close()
                else:
                    logger.error(
                        f"""Failed to list files in imported folder \
                    Imports oh the NAS in emplacement: {imported_letter_path}"""
                    )

                letter.nber_letters = tmp

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
                letters_import.state = "pending"
                if self.env.context.get("async_mode", True):
                    letters_import.with_delay()._run_analyze()
                else:
                    letters_import._run_analyze()
            return True
        else:
            # when letters selected by user, save them on NAS and call
            # super method
            for letters_import in self:
                if letters_import.data and self.env.context.get("async_mode", True):
                    for attachment in letters_import.data:
                        self._save_imported_letter(attachment)

            return super().button_import()

    @api.multi
    def button_save(self):
        """
        When saving the import_line as correspondences, move pdf file in the
        done folder on the NAS and remove image attachment (Web letter case)
        """
        try:
            # Create the letters
            super().button_save()
            # Move PDF files on the NAS
            for import_letters in self:
                if (
                        import_letters.config_id.name
                        == self.env.ref("sbc_switzerland.web_letter").name
                ):
                    for line in import_letters.import_line_ids:
                        # build part of filename, corresponding to this web
                        # import
                        # letters remove part after '-' caracter (including)
                        # corresponding to the page number
                        part_filename = (line.file_name[:-4]).split("-")[0]
                        share_nas = self.env.ref("sbc_switzerland.share_on_nas").value
                        smb_conn = self._get_smb_connection()
                        if smb_conn and smb_conn.connect(
                                SmbConfig.smb_ip, SmbConfig.smb_port
                        ):
                            imported_letter_path = self.env.ref(
                                "sbc_switzerland.scan_letter_imported"
                            ).value
                            list_paths = smb_conn.listPath(
                                share_nas, imported_letter_path
                            )

                            # loop in import folder and find pdf corresponding
                            # to this web letter and eventual attached image
                            image_ext = None
                            file_to_save = False
                            for shared_file in list_paths:
                                ext = shared_file.filename[-4:]
                                if part_filename == shared_file.filename[:-4]:
                                    if ext == ".pdf":
                                        file_to_save = True
                                    else:
                                        image_ext = ext

                            # move web letter on 'Done' folder on the NAS
                            if file_to_save:
                                filename = part_filename + ".pdf"
                                file_obj = BytesIO()
                                smb_conn.retrieveFile(
                                    share_nas, imported_letter_path + filename, file_obj
                                )
                                file_obj.seek(0)
                                self._copy_imported_to_done_letter(
                                    filename, file_obj, False
                                )
                                # delete files corresponding to web letter in
                                # 'Import'
                                try:
                                    smb_conn.deleteFiles(
                                        share_nas, imported_letter_path + filename
                                    )
                                except Exception as inst:
                                    logger.warning(
                                        f"Failed to delete pdf web letter {inst}"
                                    )

                                # image is attached to this letter so we
                                # remove it
                                if image_ext:
                                    try:
                                        smb_conn.deleteFiles(
                                            share_nas,
                                            imported_letter_path
                                            + part_filename
                                            + image_ext,
                                        )
                                    except Exception as inst:
                                        logger.warning(
                                            f"Failed to delete attached image {inst}"
                                        )

                if import_letters.manual_import:
                    self._manage_all_imported_files()

        except Exception as e:
            logger.error("Exception during letter import: {}", exc_info=True)
            # bug during import, so we remove letter sent on translation
            # platform
            self.env.clear()
            for letters in self:
                for corresp in letters.letters_ids:
                    if corresp.state == "Global Partner translation queue":
                        tc = translate_connector.TranslateConnect()
                        tc.remove_translation_with_odoo_id(corresp.id)
            raise e

        return True

    #########################################################################
    #                             PRIVATE METHODS                           #
    #########################################################################
    @job(default_channel="root.sbc_compassion")
    @related_action(action="related_action_s2b_imports")
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

        share_nas = self.env.ref("sbc_switzerland.share_on_nas").value

        smb_conn = self._get_smb_connection()
        if not self.manual_import:
            imported_letter_path = self.check_path(self.import_folder_path)
            if smb_conn and smb_conn.connect(SmbConfig.smb_ip, SmbConfig.smb_port):
                list_paths = smb_conn.listPath(share_nas, imported_letter_path)
                for shared_file in list_paths:
                    if func.check_file(shared_file.filename) == 1:
                        logger.info(
                            f"Analyzing letter {progress}" f"/{len(list_paths)}"
                        )

                        with NamedTemporaryFile() as file_obj:
                            smb_conn.retrieveFile(
                                share_nas,
                                imported_letter_path + shared_file.filename,
                                file_obj,
                            )
                            self._analyze_attachment(
                                self._convert_pdf(file_obj), shared_file.filename
                            )

                            progress += 1
                    elif func.is_zip(shared_file.filename):

                        zip_file = BytesIO()
                        # retrieve zip file from imports letters stored on
                        # NAS
                        smb_conn.retrieveFile(
                            share_nas,
                            imported_letter_path + shared_file.filename,
                            zip_file,
                        )
                        zip_file.seek(0)
                        zip_ = zipfile.ZipFile(zip_file, "r")
                        # loop over files inside zip
                        files = len(zip_.namelist())
                        for f in files:
                            logger.info(
                                f"Analyzing letter {progress}/{len(files)}"
                            )

                            self._analyze_attachment(self._convert_pdf(zip_.open(f)), f)
                            progress += 1
                smb_conn.close()
            else:
                logger.error(
                    f"Failed to list files in Imports on the NAS in \
                emplacement: {imported_letter_path}"
                )
        else:
            super()._run_analyze()

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
            file_ = BytesIO(
                base64.b64decode(attachment.with_context(bin_size=False).datas)
            )
            share_nas = self.env.ref("sbc_switzerland.share_on_nas").value

            if self.manual_import:
                imported_letter_path = (
                    self.env.ref("sbc_switzerland.scan_letter_imported").value
                    + attachment.name
                )
            else:
                imported_letter_path = (
                    self.check_path(self.import_folder_path) + attachment.name
                )

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
        share_nas = self.env.ref("sbc_switzerland.share_on_nas").value
        # to delete after treatment
        list_zip_to_delete = []
        imported_letter_path = ""
        if self.manual_import:
            imported_letter_path = self.env.ref(
                "sbc_switzerland.scan_letter_imported"
            ).value
        else:
            imported_letter_path = self.check_path(self.import_folder_path)

        smb_conn = self._get_smb_connection()
        if smb_conn and smb_conn.connect(SmbConfig.smb_ip, SmbConfig.smb_port):

            list_paths = smb_conn.listPath(share_nas, imported_letter_path)
            for shared_file in list_paths:
                if func.check_file(shared_file.filename) == 1:
                    # when this is manual import we don't have to copy all
                    # files, web letters are stored in the same folder...
                    if not self.manual_import or self.is_in_list_letter(
                            shared_file.filename
                    ):
                        file_obj = BytesIO()
                        smb_conn.retrieveFile(
                            share_nas,
                            imported_letter_path + shared_file.filename,
                            file_obj,
                        )
                        file_obj.seek(0)
                        self._copy_imported_to_done_letter(
                            shared_file.filename, file_obj, True
                        )
                elif func.is_zip(shared_file.filename):
                    zip_file = BytesIO()

                    smb_conn.retrieveFile(
                        share_nas, imported_letter_path + shared_file.filename, zip_file
                    )
                    zip_file.seek(0)
                    zip_ = zipfile.ZipFile(zip_file, "r")

                    zip_to_remove = False
                    for f in zip_.namelist():
                        # when this is manual import we are not sure that this
                        # zip contains current letters treated
                        if not self.manual_import or self.is_in_list_letter(f):
                            self._copy_imported_to_done_letter(
                                f, BytesIO(zip_.read(f)), False
                            )
                            zip_to_remove = True

                    if zip_to_remove:
                        list_zip_to_delete.append(shared_file.filename)

            # delete zip file from origin import folder on the NAS
            for filename in list_zip_to_delete:
                try:
                    smb_conn.delete_files(share_nas, imported_letter_path + filename)
                except Exception as inst:
                    logger.warning(f"Failed to delete zip file on NAS: {inst}")
            smb_conn.close()

    def is_in_list_letter(self, filename):
        """
        Check if given filename is in import letter list
        """
        for line in self.import_line_ids:
            if filename[:-4] in line.file_name:
                return True
        return False

    def _copy_imported_to_done_letter(self, filename, file_to_copy, delete_file):
        """
        Copy letter from 'imported' folder to 'done' folder on  a shared folder
        on NAS
            - filename: filename to give to saved file
            - file_to_copy: the file to copy
            - delete_file: set to true if file_to_copy must be deleted after
              the copy
        Done by Michael Sandoz 02.2016
        """
        smb_conn = self._get_smb_connection()
        if smb_conn and smb_conn.connect(SmbConfig.smb_ip, SmbConfig.smb_port):
            # Copy file in attachment in the done letter folder
            share_nas = self.env.ref("sbc_switzerland.share_on_nas").value

            # Add end path corresponding to the end of the import folder path
            end_path = ""
            if self.import_folder_path:
                end_path = (
                    self.check_path(self.import_folder_path)
                        .replace("\\", "/")
                        .replace("//", "/")
                )
                end_path = end_path.split("/")[-2] + "/"
            done_letter_path = (
                self.env.ref("sbc_switzerland.scan_letter_done").value
                + end_path
                + filename
            )

            smb_conn.storeFile(share_nas, done_letter_path, file_to_copy)

            # Delete file in the imported letter folder
            if delete_file:
                if self.manual_import:
                    imported_letter_path = (
                        self.env.ref("sbc_switzerland.scan_letter_imported").value
                        + filename
                    )
                else:
                    imported_letter_path = (
                        self.check_path(self.import_folder_path) + filename
                    )

                try:
                    smb_conn.deleteFiles(share_nas, imported_letter_path)
                except Exception as inst:
                    logger.warning("Failed to delete a file on NAS : {}".format(inst))

            smb_conn.close()
        return True

    def check_path(self, path):
        """" Add backslash at end of path if not contains ever one """
        if path and not path[-1] == "\\":
            path = path + "\\"
        return path

    def _get_smb_connection(self):
        """" Retrieve configuration SMB """
        if not (
                SmbConfig.smb_user
                and SmbConfig.smb_pass
                and SmbConfig.smb_ip
                and SmbConfig.smb_port
        ):
            return False
        else:
            return SMBConnection(
                SmbConfig.smb_user, SmbConfig.smb_pass, "openerp", "nas"
            )

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

    def _convert_pdf(self, temp_pdf_file):
        """
        Converts pdf to ensure the import is capable of reading pdf
        :param temp_pdf_file: File object
        :return: converted pdf data
        """
        temp_pdf_file.seek(0)
        gs = find_in_path("gs")
        args = [
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/default",
            "-dNOPAUSE",
            "-dQUIET",
            "-dBATCH",
        ]
        with NamedTemporaryFile() as output:
            command = [gs] + args + ["-sOutputFile=" + output.name, temp_pdf_file.name]
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            process.communicate()
            if process.returncode not in [0, 1]:
                # Convert failed, we return original pdf
                return temp_pdf_file.read()
            output.seek(0)
            return output.read()


class SmbConfig:
    """" Little class who contains SMB configuration """

    smb_user = config.get("smb_user")
    smb_pass = config.get("smb_pwd")
    smb_ip = config.get("smb_ip")
    smb_port = int(config.get("smb_port", 0))
