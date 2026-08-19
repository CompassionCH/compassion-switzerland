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
    """Two follow-up fixes for the same v14->v18 PostFinance provider
    migration gap already patched once in 18.0.1.0.4 (redirect_form_view_id):

    - That earlier fix looked up the provider via the xml_id
      payment_postfinance_flex.payment_acquirer_postfinance, which
      payment_postfinance_flex's own 18.0.5.0.0 migration later renamed to
      payment_provider_postfinance - silently turning the fix into a no-op
      on any environment where both modules migrate in that order. Look up
      the provider directly by code instead, so this doesn't depend on
      migration ordering between the two modules.
    - Separately, a real payment fails at account.payment creation with
      "Please define a payment method line on your payment.": there is no
      account.payment.method with code='postfinance' anywhere (only
      postfinance.dd, for direct debit, exists), so
      payment.provider._ensure_payment_method_line() has nothing to link
      and silently does nothing. Create the missing method, then run the
      linking for real.
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

    method = env["account.payment.method"].search(
        [("code", "=", "postfinance")], limit=1
    )
    if not method:
        method = env["account.payment.method"].create(
            {"name": "PostFinance", "code": "postfinance", "payment_type": "inbound"}
        )
        _logger.info("Created missing account.payment.method %s.", method.id)

    for provider in providers.filtered("journal_id"):
        # _ensure_payment_method_line() reads/uses journal_id as-is, but the
        # field is a stored compute whose fallback (when nothing anchors it
        # yet) can pick an arbitrary bank journal on any later registry
        # rebuild. Capture the configured journal and restore it explicitly
        # after linking, instead of trusting it survives untouched.
        configured_journal = provider.journal_id
        provider._ensure_payment_method_line()
        if provider.journal_id != configured_journal:
            provider.journal_id = configured_journal.id
        _logger.info(
            "Ensured PostFinance payment method line for provider %s (journal %s).",
            provider.id,
            provider.journal_id.id,
        )
