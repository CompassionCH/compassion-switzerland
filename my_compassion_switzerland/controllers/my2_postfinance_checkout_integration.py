##############################################################################
#
#    Copyright (C) 2025 Compassion CH (http://www.compassion.ch)
#    @author: Samuel Bachmann <zivi5@compassion.ch>
#
#    The licence is in the file __manifest__.py
#
##############################################################################
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import werkzeug

from odoo import http
from odoo.addons.payment_postfinance_flex.controllers.main import PostFinanceController
from odoo.http import request


class MyCompassionPostFinanceController(PostFinanceController):

    @http.route(
        [PostFinanceController._success_url, PostFinanceController._failed_url],
        type="http",
        auth="public",
        csrf=False
    )
    def postfinance_form_feedback(self, txnId=None, **post):
        """
        Override to process feedback, force token creation, and redirect.
        """
        try:
            super(MyCompassionPostFinanceController, self).postfinance_form_feedback(txnId, **post)
        except Exception as e:
            print(f"Standard PostFinance feedback ignored exception: {e}")

        if txnId:
            tx = request.env['payment.transaction'].sudo().browse(int(txnId))
            if tx.exists():

                if not tx.payment_token_id and tx.acquirer_id.provider == 'postfinance':
                    try:
                        self._create_postfinance_token(tx)
                        # Explicitly refresh transaction to ensure ORM sees the new token
                        tx.invalidate_cache()
                        tx = request.env['payment.transaction'].sudo().browse(int(txnId))
                    except Exception as e:
                        print(f"Failed to create PostFinance token: {e}")

                # Force processing (Standard Odoo Logic for tokens)
                if not tx.is_processed and tx.state in ['done', 'authorized']:
                    try:
                        tx._post_process_after_done()
                    except Exception as e:
                        print(f"Error processing transaction {tx.id}: {e}")

                # Create Group if Validation Success
                if tx.type == 'validation' and tx.state in ['done', 'authorized']:
                    print(f"Creating contract group for TX {tx.id}")
                    request.env['recurring.contract.group'].sudo().create_from_transaction(tx)

                # Redirect
                if tx.return_url:
                    # Append ?payment_success=True to the return URL
                    url_parts = list(urlparse(tx.return_url))
                    query = parse_qs(url_parts[4])
                    query['payment_success'] = ['True']
                    url_parts[4] = urlencode(query, doseq=True)
                    return_url_with_param = urlunparse(url_parts)
                    return werkzeug.utils.redirect(return_url_with_param)

        return werkzeug.utils.redirect("/payment/process")

    def _create_postfinance_token(self, tx):
        """
        Fetch transaction details from PostFinance to get the 'token' (Alias).
        Create a payment.token record linked to the partner.
        """
        # 1. Search Transaction at PostFinance
        search_params = {'acquirer_reference': tx.acquirer_reference}

        # NOTE: postfinance_search_transation_id is an @api.model method in the acquirer
        response = tx.acquirer_id.postfinance_search_transation_id(tx.acquirer_id.id, search_params)

        if response.get('status') == 200 and response.get('data'):
            pf_data = response['data'][0]

            # 2. Extract Token Info
            token_info = pf_data.get('token')

            if token_info:
                token_ref = token_info.get('id')

                # 3. Extract Payment Method Brand (e.g. "MasterCard", "TWINT")
                connector_config = pf_data.get('paymentConnectorConfiguration', {})
                full_method_name = connector_config.get('name', 'PostFinance Payment')

                # Cleanup: Remove provider prefix if present (e.g. "SIX Acquiring - ")
                if ' - ' in full_method_name:
                    brand_name = full_method_name.split(' - ')[-1]
                else:
                    brand_name = full_method_name

                # Requested format: token_name = MasterCard-tokenId
                token_name = f"{brand_name}-{token_ref}"
                print(f"Extracted Payment Method: {token_name} (Ref: {token_ref})")

                # Check if it already exists to avoid duplicates
                existing_token = request.env['payment.token'].sudo().search([
                    ('name', '=', token_name),
                    ('acquirer_id', '=', tx.acquirer_id.id)
                ], limit=1)

                if existing_token:
                    tx.payment_token_id = existing_token.id
                    print(f"Linked existing token {existing_token.id} to transaction {tx.id}")
                else:
                    # Create new Token
                    new_token = request.env['payment.token'].sudo().create({
                        'name': token_name,
                        'partner_id': tx.partner_id.id,
                        'acquirer_id': tx.acquirer_id.id,
                        'acquirer_ref': tx.acquirer_reference,
                        'active': True,
                    })
                    tx.payment_token_id = new_token.id
                    print(f"Created new PostFinance token: {new_token.id} for transaction {tx.id}")
        else:
            print("No token info found in PostFinance response data.")