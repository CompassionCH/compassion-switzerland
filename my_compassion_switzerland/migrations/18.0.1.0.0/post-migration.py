##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("reloading Volunteer Registration mail template with QWeb body")
    openupgrade.load_data(
        env, "my_compassion_switzerland", "data/mail_template_data.xml"
    )
