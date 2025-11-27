{
    "name": "Website Sale PostFinance Fee Extension",
    "summary": "Migrates payment fee configuration from Provider to Method for PostFinance.",
    "version": "18.0.1.0.0",
    "category": "Website/E-commerce",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-nordic",
    "development_status": "Need to be tested",

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

