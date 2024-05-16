import logging

from odoo import models

logger = logging.getLogger(__name__)


class ImportLettersLine(models.Model):
    _inherit = "import.letter.line"

    def get_correspondence_metadata(self):
        res = super().get_correspondence_metadata()
        del res["import_folder_path"]
        return res
