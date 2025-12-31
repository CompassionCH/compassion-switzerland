from odoo import http
from odoo.http import request
# Import the parent class to inherit
from odoo.addons.my_compassion.controllers.my2_donations import MyCompassionDonationsController


class MyCompassionDonationsControllerSwiss(MyCompassionDonationsController):


    @http.route('/my2/donation/add_payment_method_online', type='json', auth='user', website=True)
    def add_payment_method_online(self, **kwargs):
        """
        Override the route to force Odoo to use this class (MyCompassionDonationsControllerSwiss)
        instead of the parent class. calling super() preserves the generic logic
        but ensures 'self' refers to this class instance.
        """
        return super(MyCompassionDonationsControllerSwiss, self).add_payment_method_online(**kwargs)

    # ------------------------

    def _get_online_payment_redirect_url(self, acquirer, tx, return_url):
        """
        PostFinance Specific: Use the API to create the transaction and get the URL.
        """
        if acquirer.provider != 'postfinance':
            return super()._get_online_payment_redirect_url(acquirer, tx, return_url)

        # 1. Convert relative URL to absolute (Required by PostFinance)
        base_url = request.httprequest.host_url
        if return_url.startswith('/'):
            return_url = base_url.rstrip('/') + return_url

        # 2. Prepare Data specific for the Flex module API
        tx_values = {
            'tx_details': {
                'currency_name': tx.currency_id.name,
                'name': tx.reference,
                'partner_id': tx.partner_id.id,
            },
            'txline_details': [{
                'name': 'Validation',
                'quantity': 1,
                'type': 'PRODUCT',
                'uniqueId': 'validation',
                'amountIncludingTax': 0.0,
            }],
            # False allows the user to choose their method (Visa/Postcard) on the PostFinance page
            'postfinance_payment_method': False,
            'billing_address': {
                "city": tx.partner_id.city or '',
                "emailAddress": tx.partner_id.email or '',
                "givenName": tx.partner_id.firstname or '',
                "familyName": tx.partner_id.lastname or '',
                "postCode": tx.partner_id.zip or '',
                "street": tx.partner_id.street or '',
                "country": tx.partner_id.country_id.code or 'CH',
            }
        }

        # 3. Create Transaction on PostFinance via Flex Module
        try:
            # Calls the method defined in 'payment_postfinance_flex/models/payment.py'
            create_res = acquirer.sudo().postfinance_create_transation(acquirer.id, tx_values)

            pf_trans_id = create_res.get('trans_id')
            if not pf_trans_id:
                return False

            # Update Odoo with the external ID so we can match it later
            tx.sudo().write({'acquirer_reference': pf_trans_id})

            # 4. Get the Page URL
            url_res = acquirer.sudo().postfinance_build_payment_page_url(acquirer.id, pf_trans_id)
            return url_res.get('postfinance_redirect_url')

        except Exception as e:
            # Log error if needed
            return False