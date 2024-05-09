import logging

from odoo.tools.convert import convert_file

logger = logging.getLogger(__name__)


def migrate(cr, version):
    # Path to your XML file
    xml_file_path = "data/wordpress_cron.xml"

    try:
        # Convert and load the XML file
        convert_file(cr, "child_sync_wp", xml_file_path, {}, "init", {}, {})
        logger.info(f"Successfully loaded {xml_file_path}")
    except Exception as e:
        logger.error(f"Error loading {xml_file_path}: {str(e)}")
