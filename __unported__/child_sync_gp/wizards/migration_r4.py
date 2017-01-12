# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __openerp__.py
#
##############################################################################

import logging
from openerp import models, api
from ..models.gp_connector import GPConnect


logger = logging.getLogger(__name__)


class MigrationR4(models.TransientModel):
    """ Perform migrations after upgrading the module
    """
    _name = 'migration.r4'

    @api.model
    def perform_migration(self):
        # Only execute migration for 8.0.1.4 -> 8.0.3.0
        child_sync_module = self.env['ir.module.module'].search([
            ('name', '=', 'child_sync_gp')
        ])
        if child_sync_module.latest_version == '8.0.1.4':
            self._perform_migration()
        return True

    def _perform_migration(self):
        """
        Synchronize GP for all children
        """
        logger.info("MIGRATION 8.0.3 ----> Synchronize GP child codes.")
        # Synchronize GP
        gp = GPConnect()
        for child in self.env['compassion.child'].search([]):
            gp.transfer(self.env.uid, child.code, child.local_id)

        logger.info("MIGRATION 8.0.3 ----> Synchronize GP project codes.")
        gp.query("""
            UPDATE Projet
            SET code_projet = CONCAT(LEFT(code_projet, 2), '0',
                                     RIGHT(code_projet, 3))
            WHERE CHAR_LENGTH(code_projet) = 5;
        """)
