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
    """The redirect-form-view fix already patched once in 18.0.1.0.4 looked
    up the provider via the xml_id
    payment_postfinance_flex.payment_acquirer_postfinance, which
    payment_postfinance_flex's own 18.0.5.0.0 migration later renamed to
    payment_provider_postfinance - silently turning the fix into a no-op on
    any environment where both modules migrate in that order. Look up the
    provider directly by code instead, so this doesn't depend on migration
    ordering between the two modules.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    providers = env["payment.provider"].search([("code", "=", "postfinance")])
    if not providers:
        return

    redirect_form = env.ref(
        "payment_postfinance_flex.redirect_form", raise_if_not_found=False
    )
    if redirect_form:
        missing_redirect = providers.filtered(lambda p: not p.redirect_form_view_id)
        if missing_redirect:
            missing_redirect.redirect_form_view_id = redirect_form
            _logger.info(
                "Set the PostFinance redirect form on providers %s.",
                missing_redirect.ids,
            )
