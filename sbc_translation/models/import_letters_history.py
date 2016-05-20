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

from openerp import models, api
from . import translate_connector

logger = logging.getLogger(__name__)


class ImportLettersHistory(models.Model):
    """
    Redefine save button when problem to import
    """

    _inherit = 'import.letters.history'

    @api.multi
    def button_save(self):
        """
        save the import_line as a correspondence
        """
        try:
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
        return True
