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


def migrate(cr, version):
    """The payment.provider migrated from the v14 payment.acquirer lacks the
    redirect form view (a field set only by the module's own seed record), so
    the donation checkout never renders the redirect to PostFinance and the
    client spins forever. Point the migrated provider at the module's redirect
    form.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    provider = env.ref(
        "payment_postfinance_flex.payment_acquirer_postfinance",
        raise_if_not_found=False,
    )
    redirect_form = env.ref(
        "payment_postfinance_flex.redirect_form", raise_if_not_found=False
    )
    if provider and redirect_form and not provider.redirect_form_view_id:
        provider.redirect_form_view_id = redirect_form
        _logger.info(
            "Set the PostFinance redirect form on migrated provider %s.",
            provider.id,
        )
