# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    @author: Samuel Bachmann <samuel.bachmann02@gmail.com>
#
#    The licence is in the file __manifest__.py
#
##############################################################################

from odoo import models, api, _
import logging

_logger = logging.getLogger(__name__)


class PaymentAcquirerPostFinance(models.Model):
    _inherit = 'payment.acquirer'

    def postfinance_charge_token(self, token, amount, currency, reference, partner_id):
        """
        Server-to-Server (S2S) charge of an existing PostFinance Token.
        :param token: payment.token record
        :param amount: float
        :param currency: res.currency record
        :param reference: str (unique merchant reference, e.g. INV/2025/001)
        :param partner_id: res.partner record
        """
        self.ensure_one()

        if self.provider != 'postfinance':
            return {'success': False, 'error': 'Invalid provider'}

        # 1. Validation
        # We need the Integer ID of the token on PostFinance side (e.g., 12345678)
        # We stored this in 'acquirer_ref' during token creation.
        if not token.acquirer_ref:
            return {'success': False, 'error': 'Token has no PostFinance ID (acquirer_ref)'}

        try:
            pf_token_id = int(token.acquirer_ref)
        except ValueError:
            return {'success': False, 'error': f'Invalid Token ID format: {token.acquirer_ref}'}

        # 2. Prepare API Payload
        tx_values = {
            'currency': currency.name,
            'lineItems': [{
                'amountIncludingTax': amount,
                'name': _('Subscription Charge'),
                'quantity': 1,
                'type': 'PRODUCT',
                'uniqueId': 'recurring_charge',
                'sku': 'monthly_sub'
            }],
            'token': pf_token_id,

            # --- CONFIGURATION FOR IMMEDIATE CHARGE ---
            'autoConfirmationEnabled': True,  # Capture immediately
            'chargeRetryEnabled': False,  # Fail immediately if declined (Sync response)

            'merchantReference': reference,
            'billingAddress': {
                'country': partner_id.country_id.code or 'CH',
                'emailAddress': partner_id.email or '',
                'familyName': partner_id.lastname or partner_id.name or '',
                'givenName': partner_id.firstname or '',
            }
        }

        # 3. Call PostFinance API (Create Transaction)
        try:
            space_id = self.postfinance_api_spaceid
            uri = f"/api/transaction/create?spaceId={space_id}"

            resp = self._postfinance_send_request(self.id, 'POST', uri, json_data=tx_values)

            if resp.get('status') != 200:
                return {'success': False, 'error': resp.get('error', 'API Error')}

            data = resp.get('data', {})
            state = data.get('state')
            transaction_id = data.get('id')

            # --- STEP 4: Force Processing (If still PENDING) ---
            if state == 'PENDING':
                _logger.info(f"Transaction {transaction_id} PENDING. Attempting to process without user interaction...")

                # CORRECT ENDPOINT: For S2S token charges, we often need to "process" it.
                # Try passing the ID in the QUERY string, but remove 'tokenId'
                process_uri = f"/api/transaction/process?spaceId={space_id}&id={transaction_id}"

                # Some API versions require the transaction ID in the body, not the URL.
                # If the above 404s again, likely the endpoint is meant to be hit via the SDK service "TransactionService"
                # which usually maps to:
                process_resp = self._postfinance_send_request(self.id, 'POST', process_uri)

                # If that still returns 404 or fails, we fallback to just returning the PENDING state error.
                if process_resp.get('status') == 200:
                    data = process_resp.get('data', {})
                    state = data.get('state')

            # 5. Final State Check
            if state in ['AUTHORIZED', 'COMPLETED', 'FULFILL', 'PROCESSING']:
                return {'success': True, 'transaction_id': transaction_id, 'state': state}
            else:
                fail_reason = data.get('failureReason', {}).get('description', 'No reason provided')
                # If it is PENDING here, it usually means the Token is invalid for S2S (requires 3DS)
                # or the API requires a specific "Merchant Initiated" flag in the paymentConnectorConfiguration.
                return {
                    'success': False,
                    'error': f"State: {state} | Reason: {fail_reason}",
                    'transaction_id': transaction_id
                }

        except Exception as e:
            _logger.exception("Exception during PostFinance Token Charge")
            return {'success': False, 'error': str(e)}
