# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    Releasing children from poverty in Jesus' name
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging
from openupgradelib import openupgrade


_logger = logging.getLogger(__name__)


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    if not version:
        return

    # Compute geo_point at migration
    missing_geo = env['res.partner'].search([
        ('partner_latitude', '=', False),
        ('partner_longitude', '=', False),
        ('city', '!=', False),
        ('country_id', '!=', False)
    ])
    _logger.info("computing geolocation for %s partners", len(missing_geo))
    missing_geo.compute_geopoint()
    env['advocate.details'].search([]).set_geo_point()
