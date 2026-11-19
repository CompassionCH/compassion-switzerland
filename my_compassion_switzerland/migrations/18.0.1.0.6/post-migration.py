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
    """Two follow-up fixes for the v14->v18 PostFinance provider migration gap
    already patched once in 18.0.1.0.4 (redirect_form_view_id):

    - That earlier fix resolved the provider through the xml_id
      payment_postfinance_flex.payment_acquirer_postfinance, which the module
      later renamed to payment_provider_postfinance - silently turning the fix
      into a no-op. Look the provider up by code instead.
    - A real payment fails at account.payment creation with "Please define a
      payment method line on your payment.": no account.payment.method with
      code='postfinance' exists (only postfinance.dd, for direct debit), so
      _ensure_payment_method_line() has nothing to link and returns silently.
      That method is normally created by the provider module's post_init_hook,
      which runs on install only - never on the v14->v18 upgrade.
      _setup_provider() is that same core setup, and it is idempotent.

    The journal must then be set explicitly. journal_id is a non-stored compute
    that, as long as no payment method line exists, falls back to the first bank
    journal by sequence - so merely reading it wires the provider to an
    arbitrary bank journal. Online payments belong on the Web clearing journal
    (no bank account attached), not on a real bank journal used for statement
    reconciliation.
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

    env["payment.provider"]._setup_provider("postfinance")

    for provider in providers:
        journal = env["account.journal"].search(
            [("code", "=", "WEB"), ("company_id", "=", provider.company_id.id)], limit=1
        )
        if not journal:
            _logger.warning(
                "No WEB journal in company %s: set the journal on the PostFinance "
                "provider manually.",
                provider.company_id.id,
            )
            continue
        provider.journal_id = journal
        _logger.info(
            "Linked PostFinance provider %s to journal %s.", provider.id, journal.code
        )
