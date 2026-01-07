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
            'autoConfirmationEnabled': True,
            'chargeRetryEnabled': False,

            'completionBehavior': 'COMPLETE_IMMEDIATELY',


            'merchantReference': reference,
            'billingAddress': {
                'country': partner_id.country_id.code or 'CH',
                'emailAddress': partner_id.email or '',
                'familyName': partner_id.lastname or partner_id.name or '',
                'givenName': partner_id.firstname or '',
            }
        }# 3. Call PostFinance API (Create Transaction)
        # Note: If this still stays PENDING, we might need a second call to /transaction/process
        try:
            space_id = self.postfinance_api_spaceid
            uri = f"/api/transaction/create?spaceId={space_id}"

            resp = self._postfinance_send_request(
                self.id,
                'POST',
                uri,
                json_data=tx_values
            )

            if resp.get('status') != 200:
                return {'success': False, 'error': resp.get('error', 'API Error')}

            data = resp.get('data', {})
            state = data.get('state')
            transaction_id = data.get('id')

            # --- STEP 4: Force Processing (If still PENDING) ---
            # Sometimes 'create' just drafts it. We must explicitly 'process' it with the token.
            if state == 'PENDING':
                _logger.info(f"Transaction {transaction_id} is PENDING. Attempting to force process...")

                process_uri = f"/api/transaction/process?spaceId={space_id}&id={transaction_id}&tokenId={pf_token_id}"

                # We call the PROCESS endpoint
                # Note: Some APIs require 'processWithoutUserInteraction' or similar
                process_resp = self._postfinance_send_request(
                    self.id,
                    'POST', # or GET depending on specific endpoint version, usually POST for actions
                    process_uri
                )

                if process_resp.get('status') == 200:
                    data = process_resp.get('data', {})
                    state = data.get('state')

            # Final Check
            if state in ['AUTHORIZED', 'COMPLETED', 'FULFILL', 'PROCESSING']:
                return {'success': True, 'transaction_id': transaction_id, 'state': state}
            else:
                fail_reason = data.get('failureReason', {}).get('description', 'No reason provided')
                return {'success': False, 'error': f"State: {state} | Reason: {fail_reason}", 'transaction_id': transaction_id}

        except Exception as e:
            _logger.exception("Exception during PostFinance Token Charge")
            return {'success': False, 'error': str(e)}
