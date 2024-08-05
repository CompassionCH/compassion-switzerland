import csv
import logging
from openupgradelib import openupgrade
from odoo.tools import file_open

_logger = logging.getLogger(__name__)


@openupgrade.migrate()
def migrate(env, version):
    file_path = "sbc_switzerland/data/supporter_letters_content_utf.csv"
    with file_open(file_path) as file:
        reader = csv.DictReader(file)
        for row in reader:
            letter = env["correspondence"].search([
                ('kit_identifier', '=', row['Kit Identifier'])])
            if letter and not letter.original_text:
                _logger.info(f"Processing row {reader.line_num}")
                letter.write({
                    'english_text': row['English Text'],
                    'translated_text': row['Final Translated Text'],
                    'original_text': row['Original Text']
                })
                letter.create_text_boxes()
