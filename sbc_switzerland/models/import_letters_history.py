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
import traceback
from pathlib import Path

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.tools.config import config
from odoo.addons.queue_job.job import job, related_action

logger = logging.getLogger(__name__)

try:
    from PyPDF2 import PdfFileWriter, PdfFileReader
    from PyPDF2.pdf import PageObject
    import pysftp
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
            key = pysftp.RSAKey(data=base64.decodebytes(key_data.encode("utf-8")))
            cnopts.hostkeys.add(config.get("sftp_ip"), "ssh-rsa", key)
        except:
            cnopts.hostkeys = None
            logger.warning(
                "No hostkeys defined in StfpConnection. Connection will be unsecured."
                "Please configure parameter sbc_switzerland.nas_ssh_key"
                "with ssh_key data.")

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
    _inherit = "import.letters.history"

    manual_import = fields.Boolean("Manual import", default=False)

    @api.onchange("data", "import_folder_path")
    def _compute_nber_letters(self):
        for letter in self:
            try:
                with letter._get_connection() as sftp:
                    letter.nber_letters = len(sftp.listdir(letter.import_folder_path))
            except (FileNotFoundError, TypeError):
                letter.nber_letters = 0

    def unlink(self):
        running_job = self.env["queue.job"].search_count([
            ("model_name", "=", self._name),
            ("state", "not in", ["done", "failed", "cancelled"]),
            ("record_ids", "in", self.ids)
        ])
        if running_job:
            raise UserError(_(
                "The import is currently analyzing files and cannot be removed. "
                "Try again later."))
        return super().unlink()

    def _get_connection(self):
        key = self.env.ref("sbc_switzerland.nas_ssh_key").value
        share = self.env.ref("sbc_switzerland.share_on_nas").value
        return SftpConnection(key).get_connection(share)

    def sftp_generator(self):
        """
        Generator function for the sftp imports
        Read the files from the specified stfp directory and analyse them

        yield:
            int: the current step in the analysis
            int: the current last step for the analysis
            str: the name of the file analysed
        """
        try:
            import_letter_path = Path(self.import_folder_path)
            imported_letter_path = Path(self.env.ref("sbc_switzerland.scan_letter_done").value)
        except TypeError:
            return
        try:
            with self._get_connection() as sftp:
                files = sftp.listdir(str(import_letter_path))
                for i, file in enumerate(files):
                    file = Path(file)
                    import_full_path = str(import_letter_path / file)
                    imported_full_path = str(imported_letter_path / file)

                    yield i + 1, len(files), import_full_path

                    pdf_data = sftp.open(import_full_path).read()
                    self._analyze_pdf(pdf_data, file)

                    try:
                        sftp.rename(import_full_path, imported_full_path)
                    except Exception as e:
                        logger.warning(f"Failed to move a file on NAS :\n{traceback.format_exc()}")
        except (AssertionError, IOError) as e:
            logger.error("Could not establish connection with sftp server")
            return

    @job(default_channel="root.sbc_compassion")
    @related_action(action="related_action_s2b_imports")
    def run_analyze(self):
        """
        Redefine the run_analyze function to handle both the manual import case and the sftp import case
        """
        if not self.manual_import:
            return super().run_analyze(self.sftp_generator)
        else:
            return super().run_analyze()
