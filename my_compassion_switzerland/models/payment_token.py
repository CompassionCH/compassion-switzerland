##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    @author: Samuel Bachmann <samuel.bachmann02@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

import logging
from odoo import models, api, fields

_logger = logging.getLogger(__name__)


class PaymentToken(models.Model):
    _inherit = 'payment.token'

    @api.model
    def create_or_find_postfinance_token(self, tx):
        """
        Custom logic to deduplicate tokens.
        1. Calls API to get the real Token ID.
        2. Checks if we already have a token with this ID.
        3. Returns existing token OR creates a new one.
        """
        # A. Fetch Data from PostFinance
        search_params = {"acquirer_reference": tx.acquirer_reference}
        response = tx.acquirer_id.postfinance_search_transation_id(
            tx.acquirer_id.id, search_params
        )

        if response.get("status") != 200 or not response.get("data"):
            _logger.error("PostFinance: API search failed for tx %s", tx.acquirer_reference)
            return None

        pf_data = response["data"][0]
        token_info = pf_data.get("token")

        if not token_info or not token_info.get("id"):
            _logger.warning("PostFinance: No token info found for tx %s", tx.id)
            return None

        token_pf_id = str(token_info["id"])

        # B. DEDUPLICATION: Check if this token already exists
        existing_token = self.search([
            ('acquirer_ref', '=', token_pf_id),
            ('acquirer_id', '=', tx.acquirer_id.id),
            ('partner_id', '=', tx.partner_id.id)
            # Note: We check partner_id to be safe, though token IDs are usually unique per space
        ], limit=1)

        if existing_token:
            if not existing_token.active:
                existing_token.active = True  # Reactivate if it was archived
            return existing_token

        # C. CREATE: Prepare Data for New Token
        # Extract Brand Name
        connector_config = pf_data.get("paymentConnectorConfiguration", {})
        full_method_name = connector_config.get("name", "PostFinance Payment")
        brand_name = full_method_name.split(" - ")[-1] if " - " in full_method_name else full_method_name

        token_name = f"{brand_name} {token_pf_id[-4:]}"  # e.g. "Visa 1234" (Cleaner than full ID)

        return self.create({
            "name": token_name,
            "partner_id": tx.partner_id.id,
            "acquirer_id": tx.acquirer_id.id,
            "acquirer_ref": token_pf_id,
            "active": True,
        })