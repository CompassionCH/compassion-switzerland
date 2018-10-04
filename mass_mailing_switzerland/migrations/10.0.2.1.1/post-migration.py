# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from openupgradelib import openupgrade

logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Try to catch the opt_out date for partners
    opt_out_partners = env['res.partner'].search([('opt_out', '=', True)])
    count_log = 0
    count_not_found = 0
    for partner in opt_out_partners:
        opt_out_log = env['auditlog.log.line'].search([
            ('field_id.model', '=', 'res.partner'),
            ('field_id.name', '=', 'opt_out'),
            ('log_id.res_id', '=', partner.id),
            ('new_value', '=', 'True')
        ], order='id desc', limit=1)
        if opt_out_log:
            partner.date_opt_out = opt_out_log.create_date
            count_log += 1
        else:
            partner.date_opt_out = partner.create_date
            count_not_found += 1
    logger.info("Updated %s partners with opt_out date from logs", count_log)
    logger.info("Updated %s partners but opt_out date was not found",
                count_not_found)
