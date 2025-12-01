{
    "name": "Website Sale Fee Extension",
    "summary": "Migrates payment fee configuration from payment provider to payment method.",
    "version": "18.0.1.0.0",
    "category": "Website/E-commerce",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-nordic",
    "development_status": "Alpha",

    "description": """

    Description
    --------------------------------
    This module is an extension that adapts the management of payment fees (`fee`) from
    the OCA module `website_sale_charge_payment_fee` for payment methods.

    Installation Instructions
    --------------------------------
    1.  **Prerequisite:** First, install the OCA module `eCommerce: charge payment fee`
                          (`website_sale_charge_payment_fee`).
    
    2.  **Verification:** Ensure that no fees are configured in the
                          **Payment Providers** (`payment.provider`).
    
    3.  **Installation:** Install this module (`website_sale_payment_fee_extension`).
    
    4.  **Configuration:** Configure the fees (`fee`) directly within the specific
                           **Payment Methods**.
    
    Technical Details
    ------------------
    This module hides the fee configuration fields on the `payment.provider` model but
    does not delete them. This technical choice to hide the fields (rather than deleting
    them or modifying the OCA code) is made with the following goals:
        * **Facilitate Updates:** Allows for easy updating of the OCA module
                                  `website_sale_charge_payment_fee` when new versions
                                  are released.
    
        * **Improve User Experience:** Avoid confusing the user with two different
                                       places to configure fees (the Provider and the
                                       Method) by hiding the old configuration source.
    
        * **Prevent Bugs:** Reduce the risk of side effects (`side effects`) and new
                            sources of bugs that would occur if two competing fee
                            mechanisms were active.

    Limitations and Technical Notes
    -------------------------------
    **1. Currency Conversion Issue (Fixed Fees)** 
    The implementation of currency conversion for fixed fees (`fixed fee`) is incomplete
    in this context. Consequently, conversion issues may arise if the fee currency
    differs from the cart currency.

    * **Impact:** If a fee of **10 EUR** is applied to a cart in **Swedish Krona (SEK)**
                  without a valid exchange rate in the system, the final fee amount will
                  be erroneously calculated as **10 SEK** (1:1 rate) instead of the
                  converted value.

    * **Resolution:**
    * **Configuration Required:** It is imperative that Odoo's automatic
                                  **CurrencyRate** update service is correctly
                                  configured and active (`Currency Rate Update` cron
                                  job) to guarantee accurate conversions.

    * **Development Path:** A more robust technical solution would require **redefining
                            the `sale.order` model** and rewriting the fee calculation
                            method (`update_fee_line` or equivalent) to force a more
                            reliable retrieval of the target cart currency
                            (`pricelist_id.currency_id` or `website_id.currency_id`).

    * **Test Scope:** The functionality has not been exhaustively tested across all
                      possible currency scenarios. Rigorous manual testing is required
                      in a production or pre-production environment to ensure the
                      accuracy of conversion calculations for all specific use cases.

    **2. Multi-Company Compatibility**
    The proper functioning of fees and currency conversions in a **Multi-Company**
    environment is not supported by this extension module.
    * **Issue:** Configuration problems may arise if the fee currency, the pricelist
                 currency, and the exchange rates are not correctly linked to the
                 transaction's associated company. Rigorous testing is required when
                 using this module in a multi-company context.

    * **Note:** The proper functioning of fees and conversions heavily relies on an
                impeccable configuration of currencies and pricelists in Odoo for this
                environment.
    """,

    "depends": [
        "website_sale_charge_payment_fee",
        "payment",
        "website_sale",
    ],

    "data": [
        "views/payment_views.xml",
        "views/website_sale_extension_templates.xml",
    ],

    "installable": True,
    "auto_install": False,
}

