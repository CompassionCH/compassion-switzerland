{
    "name": "Website Sale PostFinance Fee Extension",
    "summary": "Migrates payment fee configuration from Provider to Method for PostFinance.",
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
    the OCA module `website_sale_charge_payment_fee` for PostFinance payment methods.

    Installation Instructions
    --------------------------------
    1.  **Prerequisite:** First, install the OCA module `eCommerce: charge payment fee`
                          (`website_sale_charge_payment_fee`).
    
    2.  **Verification:** Ensure that no fees are configured in the **Payment Providers**
                          (`payment.provider`).
    
    3.  **Installation:** Install this module (`website_sale_postfinance_fee_extension`).
    
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
    """,

    "depends": [
        "website_sale_charge_payment_fee",
        "payment_postfinance_flex",
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

