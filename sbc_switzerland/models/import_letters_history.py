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
    from smb.smb_structs import OperationFailure
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PyPDF2.pdf import PageObject
    import pysftp
    from pysftp import RSAKey
except ImportError:
    logger.warning("Please install python dependencies.")


class SftpConnection:
    """
    Class helper used to handle connection between server and SFTP server.
    """

    def __init__(self, key_data=None):
        self.sftp_config = {
            "username": config.get("sftp_user"),
            "password": config.get("sftp_pwd"),
            "host": config.get("sftp_ip"),
            "port": int(config.get("sftp_port", 22))
        }

        self.credential_ok = all(self.sftp_config.values())

        if not self.credential_ok:
            logger.error(
                """
                Missing credentials for sftp connection to NAS. 
                Please update configuration file with :
                - sftp_user
                - sftp_pwd
                - sftp_ip
                - sftp_port (default 22)
                """
            )

        cnopts = pysftp.CnOpts()

        try:
            key = RSAKey(data=base64.decodebytes(key_data.encode('utf-8')))
            cnopts.hostkeys.add(config.get("sftp_ip"), "ssh-rsa", key)
        except:
            cnopts.hostkeys = None
            logger.warning(
                "No hostkeys defined in StfpConnection. Connection will be unsecured. "
                "Please configure parameter sbc_switzerland.nas_ssh_key with ssh_key data.")

        self.sftp_config.update({"cnopts": cnopts})

    def get_connection(self, starting_dir=None):
        """
        Use instance config to start a connection with sftp server
        raise AssertionError if credential are not set or IOError if
        starting_dir is not None and points to a not existing directory
        :param starting_dir: (optional) starting dir for the connection
        :return: Return a pysftp connection object
        """

        assert self.credential_ok, "Missing credentials for sftp connection to NAS."

        conn = pysftp.Connection(**self.sftp_config)
        if starting_dir:
            conn.chdir(starting_dir)

        return conn


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

        # files are not selected by user so we find them on NAS
        count_from_nas_letters = self.filtered(lambda x:
                                               (x.state and x.state == "draft") and not x.manual_import)

        for letter in self.filtered(lambda x: x not in count_from_nas_letters):
            super(ImportLettersHistory, letter)._compute_nber_letters()

        # avoid setting up smtp connection if unneeded
        if not len(count_from_nas_letters):
            return

        sftp_con_handler = SftpConnection(self.env.ref("sbc_switzerland.nas_ssh_key").value)
        sftp = None
        try:
            sftp = sftp_con_handler.get_connection()
        except (AssertionError, IOError) as e:
            logger.error("Could not establish connection with sftp server")
            count_from_nas_letters.write({"nber_letters": 0})
            return

        for letter in count_from_nas_letters:
            # folder 'Imports' counter
            imported_letter_path = letter.check_path(letter.import_folder_path)

            if not imported_letter_path:
                logger.error("Failed to list files in imported folder due to unset import folder path")
                letter.nber_letters = 0
                continue

            tmp = 0
            with sftp.cd(self.env.ref("sbc_switzerland.share_on_nas").value):

                try:
                    list_paths = sftp.listdir(imported_letter_path)
                except FileNotFoundError:
                    logger.error("--------------- PATH NOT CORRECT ---------------")
                    list_paths = []

                for shared_file in list_paths:
                    if func.check_file(shared_file) == 1:
                        tmp += 1
                    elif func.is_zip(shared_file):
                        logger.debug(
                            "File to retrieve:"
                            f" {imported_letter_path + shared_file}"
                        )

                        file_obj = BytesIO()
                        sftp.getfo(
                            imported_letter_path + shared_file,
                            flo=file_obj,
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
                                    + shared_file
                                    + ")"
                                )
                            )
                        except zipfile.LargeZipFile:
                            raise exceptions.UserError(
                                _(
                                    "Zip64 is not supported("
                                    + shared_file
                                    + ")"
                                )
                            )

            letter.nber_letters = tmp

        sftp.close()

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

                    with SftpConnection(self.env.ref("sbc_switzerland.nas_ssh_key").value).get_connection(
                            self.env.ref("sbc_switzerland.share_on_nas").value) as sftp:

                        imported_letter_path = self.env.ref("sbc_switzerland.scan_letter_imported").value

                        # look for pdfs and images to remove
                        list_files = [l for l in sftp.listdir(imported_letter_path) if
                                      l[:-4] in  # could be pdf or image
                                      map(lambda x: x[:-4].split("-")[0],  # lines are store in multiple part
                                          import_letters.import_line_ids.mapped('file_name'))]
                        try:
                            for file_to_remove in list_files:
                                sftp.remove(imported_letter_path + file_to_remove)
                        except Exception as inst:
                            logger.warning(f"Failed to delete pdf web letter {inst}")

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

        if self.manual_import:
            return super()._run_analyze()

        # keep track of file names to detect duplicates
        # file_name_history = []
        logger.info("Imported letters analysis started...")
        progress = 1

        imported_letter_path = self.check_path(self.import_folder_path)
        try:
            with SftpConnection(self.env.ref("sbc_switzerland.nas_ssh_key").value).get_connection(
                    self.env.ref("sbc_switzerland.share_on_nas").value) as sftp:
                list_paths = sftp.listdir(imported_letter_path)
                for shared_file in list_paths:

                    logger.info(f"Analyzing letter {progress}" f"/{len(list_paths)}")

                    if func.check_file(shared_file) == 1:

                        with NamedTemporaryFile() as file_obj:
                            sftp.getfo(
                                imported_letter_path + shared_file,
                                file_obj,
                            )
                            self._analyze_attachment(
                                self._convert_pdf(file_obj), shared_file
                            )

                            progress += 1
                    elif func.is_zip(shared_file):

                        zip_file = BytesIO()
                        # retrieve zip file from imports letters stored on NAS
                        sftp.getfo(
                            imported_letter_path + shared_file,
                            zip_file,
                        )
                        zip_file.seek(0)
                        zip_ = zipfile.ZipFile(zip_file, "r")
                        # loop over files inside zip
                        files = zip_.namelist()
                        for f in files:
                            logger.info(
                                f"Analyzing letter {progress}/{len(files)}"
                            )

                            self._analyze_attachment(self._convert_pdf(zip_.open(f)), f)
                            progress += 1

        except (AssertionError, IOError) as e:
            logger.error("Could not establish connection with sftp server")
            return

        # remove all the files (now they are inside import_line_ids)
        self.data.unlink()
        self._manage_all_imported_files()
        self.import_completed = True
        logger.info("Imported letters analysis completed.")

    def _manage_all_imported_files(self):
        """
        File management at the end of correct import:
            - Save files in their final location on the NAS
            - Delete files from their import location on the NAS
        Done by Michael Sandoz 02.2016
        """

        imported_letter_path = ""
        if self.manual_import:
            imported_letter_path = self.env.ref(
                "sbc_switzerland.scan_letter_imported"
            ).value
        else:
            imported_letter_path = self.import_folder_path

        imported_letter_path = self.check_path(imported_letter_path)

        with SftpConnection(self.env.ref("sbc_switzerland.nas_ssh_key").value).get_connection(
                self.env.ref("sbc_switzerland.share_on_nas").value) as sftp:

            for shared_file in sftp.listdir(imported_letter_path):

                if func.check_file(shared_file) == 1:
                    # when this is manual import we don't have to copy all
                    # files, web letters are stored in the same folder...
                    if not self.manual_import or self.is_in_list_letter(shared_file):
                        try:
                            sftp.remove(imported_letter_path + shared_file)
                        except Exception as inst:
                            logger.warning("Failed to delete a file on NAS : {}".format(inst))

                elif func.is_zip(shared_file):
                    zip_file = BytesIO()

                    sftp.getfo(
                        imported_letter_path + shared_file, zip_file
                    )
                    zip_file.seek(0)
                    zip_ = zipfile.ZipFile(zip_file, "r")

                    zip_to_remove = False
                    for f in zip_.namelist():
                        # when this is manual import we are not sure that this
                        # zip contains current letters treated
                        if not self.manual_import or self.is_in_list_letter(f):
                            zip_to_remove = True

                    if zip_to_remove:
                        try:
                            sftp.remove(imported_letter_path + shared_file)
                        except Exception as inst:
                            logger.warning("Failed to delete a file on NAS : {}".format(inst))

    def is_in_list_letter(self, filename):
        """
        Check if given filename is in import letter list
        """
        for line in self.import_line_ids:
            if filename[:-4] in line.file_name:
                return True
        return False

    def check_path(self, path):
        """" Add backslash at end of path if not contains ever one """
        if path and not path[-1] == "/":
            path = path + "/"
        return path

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
