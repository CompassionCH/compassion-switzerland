#    Copyright (C) 2026 Compassion CH (http://www.compassion.ch)
#    License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Compassion CH - HR Sign OCA",
    "summary": "Sign requests on employees: paper signatures, signed PDF on the "
    "employee",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "category": "Human Resources",
    "author": "Compassion CH",
    "website": "https://github.com/CompassionCH/compassion-switzerland",
    "depends": [
        "hr",
        "sign_oca",  # OCA/sign
    ],
    "data": [
        "security/ir.model.access.csv",
        "wizards/sign_oca_request_paper_views.xml",
        "views/sign_oca_request_views.xml",
        "views/hr_employee_views.xml",
    ],
    "installable": True,
}
