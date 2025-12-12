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

from odoo import http, _
from odoo.addons.payment_postfinance_flex.controllers.main import PostFinanceController
from odoo.addons.test_impex.tests.test_load import message
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
        Override to process feedback, force local saving of token_ID and redirect.
        """
        try:
            super(MyCompassionPostFinanceController, self).postfinance_form_feedback(txnId, **post)
        except Exception:
            pass

        if not txnId:
            return werkzeug.utils.redirect("/payment/process")

        tx = request.env['payment.transaction'].sudo().browse(int(txnId))
        if not tx.exists():
            return werkzeug.utils.redirect("/payment/process")

        # Create PostFinance token if missing
        if not tx.payment_token_id and tx.acquirer_id.provider == 'postfinance':
            try:
                self._create_postfinance_token(tx)
                # Ensure the newly created token is visible in current request
                tx.invalidate_cache()
                tx = request.env['payment.transaction'].sudo().browse(int(txnId))
            except Exception:
                pass

        # Force Odoo standard post-processing for tokenized payments
        if not tx.is_processed and tx.state in ['done', 'authorized']:
            try:
                tx._post_process_after_done()
            except Exception:
                pass

        # Create recurring contract group for validation transactions
        group = None
        message = ""
        if tx.type == 'validation' and tx.state in ['done', 'authorized']:
            group, message = request.env['recurring.contract.group'].sudo().create_from_transaction(tx)

        # Determine status and message from the method result
        if tx.return_url:
            if group and group.id:
                if message == "This payment method is already saved.":
                    status = 'Already Saved'
                else:
                    status = 'Success'
            else:
                status = 'Error'

            # Build query parameters
            url_parts = list(urlparse(tx.return_url or '/my/donations'))
            query = parse_qs(url_parts[4])

            query.update({
                'payment_method_result': [status],
                'payment_method_message': [message],
            })

            url_parts[4] = urlencode(query, doseq=True)
            return_url = urlunparse(url_parts)
            return werkzeug.utils.redirect(return_url)

        return werkzeug.utils.redirect("/payment/process")

    def _create_postfinance_token(self, tx):
        """
        Fetch transaction details from PostFinance to get the 'token' (Alias).
        Create or link a payment.token record to the partner.
        """
        search_params = {'acquirer_reference': tx.acquirer_reference}

        response = tx.acquirer_id.postfinance_search_transation_id(tx.acquirer_id.id, search_params)

        if response.get('status') != 200 or not response.get('data'):
            return

        pf_data = response['data'][0]
        token_info = pf_data.get('token')

        if not token_info or not token_info.get('externalId'):
            return

        token_ref = token_info['externalId']

        # Extract clean payment method brand (e.g. "MasterCard", "TWINT")
        connector_config = pf_data.get('paymentConnectorConfiguration', {})
        full_method_name = connector_config.get('name', 'PostFinance Payment')
        brand_name = full_method_name.split(' - ')[-1] if ' - ' in full_method_name else full_method_name

        token_name = f"{brand_name}_{token_ref}"

        # Reuse existing token to avoid duplicates
        existing_token = request.env['payment.token'].sudo().search([
            ('name', '=', token_name),
            ('acquirer_id', '=', tx.acquirer_id.id)
        ], limit=1)

        if existing_token:
            tx.payment_token_id = existing_token.id
        else:
            # Create new payment.token
            new_token = request.env['payment.token'].sudo().create({
                'name': token_name,
                'partner_id': tx.partner_id.id,
                'acquirer_id': tx.acquirer_id.id,
                'acquirer_ref': tx.acquirer_reference,
                'active': True,
            })
            tx.payment_token_id = new_token.id
