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
        Creates and charges a transaction using an existing PostFinance Token (Alias).
        This is a Server-to-Server (S2S) call.
        """
        self.ensure_one()

        # Verify provider
        if self.provider != 'postfinance':
            return {'success': False, 'error': _('Invalid provider for this method.')}

        # 1. Prepare Transaction Data
        # We must include the 'token' field with the externalId (acquirer_ref)
        # and 'autoConfirmationEnabled' to true for immediate charge.

        # Note: You might need to adjust 'lineItems' depending on your tax configuration.
        # Ideally, this should match the invoice lines, but a summary line works for charging.
        tx_values = {
            'currency': currency.name,
            'lineItems': [{
                'amountIncludingTax': amount,
                'name': _('Subscription Charge'),
                'quantity': 1,
                'type': 'PRODUCT',
                'uniqueId': 'subscription_charge',
                'sku': 'recurring_sub'
            }],
            # The token ID from PostFinance is stored in token.acquirer_ref
            # Ensure token.acquirer_ref contains the Integer ID (e.g. 12345), not a string ref if possible.
            'token': int(token.acquirer_ref) if token.acquirer_ref.isdigit() else token.acquirer_ref,
            'autoConfirmationEnabled': True,  # Important: Charge immediately
            'merchantReference': reference,
            'billingAddress': {
                'country': partner_id.country_id.code or 'CH',
                'emailAddress': partner_id.email
            },
            # Optional: Link to the customer if you synced them
            # 'customerId': partner_id.id
        }

        # 2. Call API
        try:
            space_id = self.postfinance_api_spaceid
            uri = "/api/transaction/create?spaceId=%s" % space_id

            # Reusing your existing helper _postfinance_send_request from the base module
            resp = self._postfinance_send_request(
                self.id,
                'POST',
                uri,
                json_data=tx_values
            )

            if resp.get('status') == 200:
                data = resp.get('data', {})
                state = data.get('state')

                # Check for successful charge states
                if state in ['AUTHORIZED', 'COMPLETED', 'FULFILL']:
                    return {
                        'success': True,
                        'transaction_id': data.get('id'),
                        'state': state
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Payment State: {state}",
                        'transaction_id': data.get('id')
                    }
            else:
                return {'success': False, 'error': f"API Error: {resp.get('error')}"}

        except Exception as e:
            _logger.exception("Error during PostFinance Token Charge")
            return {'success': False, 'error': str(e)}