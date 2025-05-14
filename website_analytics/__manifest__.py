{
    'name': "Website Analytics",
    'summary': "Module d'affichage de données Google Analytics dans Odoo",
    'description': """
        Ce module permet d'intégrer les données de Google Analytics dans Odoo
        et d'afficher des graphiques.
    """,
    'author': "Web Pro Craft",
    'website': "https://webprocraft.ch",
    'category': 'Analytics',
    'language': '1.0',
    'depends': [
        "crm_compassion",
        "partner_auto_match",
        "sponsorship_sub_management",
        "account_banking_mandate",
        "partner_compassion",
        "account_statement_completion",
        "account_reconcile_compassion",
        "gift_compassion",
        "web_notify",
        "sbc_compassion",
        "website",
        "base",
        "web",
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'demo': [
        'demo/demo.xml',
    ],
}
