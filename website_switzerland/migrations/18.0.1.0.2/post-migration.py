##############################################################################
#
#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    @author: Daniel Palumbo <dpalumbo@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Reactivate cart_address (T3464).

    This view replaces the checkout's single "Full name" field with separate
    firstname/lastname inputs, matching _get_mandatory_address_fields()'s
    requirement (also overridden in this module) for firstname/lastname
    instead of name/phone. Found archived (active=False) with nothing else
    superseding it - the checkout form fell back to the stock "Full name"
    field, which can never satisfy that requirement, so every address
    submission failed validation. The JS's error-highlighting silently
    no-ops on fields the form doesn't have, so the "Continue checkout"
    button appeared to do nothing.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    view = env.ref("website_switzerland.cart_address", raise_if_not_found=False)
    if view and not view.active:
        view.active = True
        _logger.info("Reactivated website_switzerland.cart_address (view %s).", view.id)
