##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Noé Berdoz <nberdoz@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

SWISS_PORTAL_VALUES = {
    "data_change_notification_email": "sds_requests@compassion.ch",
    "sponsor_child_url": "https://compassion.ch/parrainer-un-enfant",
}

LEGACY_PARAMETER_KEYS = [
    "my_compassion.data_change_notification_email",
    "my_compassion.sponsor_child_url",
]


def migrate(cr, version):
    """The portal settings moved from instance-global system parameters to
    per-website fields (a multi-company instance runs one portal website per
    country). Write the Swiss values on the MyCompassion websites and drop the
    now-unused parameters. This module only installs on the Swiss instance,
    so every flagged website here is Swiss.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    websites = env["website"].search([("is_my_compassion", "=", True)])
    if websites:
        websites.write(SWISS_PORTAL_VALUES)
        _logger.info(
            "Set the Swiss portal contact values on websites %s.", websites.ids
        )
    parameters = (
        env["ir.config_parameter"].sudo().search([("key", "in", LEGACY_PARAMETER_KEYS)])
    )
    if parameters:
        parameters.unlink()
