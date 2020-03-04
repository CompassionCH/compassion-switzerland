# Copyright 2018 Compassion Suisse
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "MIS Builder unpaid invoice",
    "summary": """
        unpaid invoice for MIS Builder""",
    "version": "11.0.1.0.0",
    "license": "AGPL-3",
    "author": "Odoo Community Association (OCA), Compassion Switzerland",
    "website": "https://github.com/OCA/mis-builder",
    "depends": ["mis_builder", "account", ],
    "data": ["security/mis_unpaid_invoice.xml", "views/mis_unpaid_invoice.xml", ],
    "installable": True,
}
