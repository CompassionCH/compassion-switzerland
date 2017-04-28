# -*- encoding: utf-8 -*-
##############################################################################
#
#       ______ Releasing children from poverty      _
#      / ____/___  ____ ___  ____  ____ ___________(_)___  ____
#     / /   / __ \/ __ `__ \/ __ \/ __ `/ ___/ ___/ / __ \/ __ \
#    / /___/ /_/ / / / / / / /_/ / /_/ (__  |__  ) / /_/ / / / /
#    \____/\____/_/ /_/ /_/ .___/\__,_/____/____/_/\____/_/ /_/
#                        /_/
#                            in Jesus' name
#
#    Copyright (C) 2015-2017 Compassion CH (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'Tailor Sponsorships to Compassion CH needs',
    'version': '8.0.3.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['sponsorship_tracking', 'partner_compassion',
                'partner_communication', 'account_statement_completion'],
    'data': [
        'data/product.xml',
        'data/completion_rules.xml',
        'data/payment_terms.xml',
        'workflow/sds_workflow.xml',
        'security/ir.model.access.csv',
        'views/account_invoice_view.xml',
        'views/res_partner_view.xml',
        'views/statement_view.xml',
        'views/contract_view.xml',
    ],
    'js': ['static/src/js/sponsorship_tracking_kanban.js'],
    'demo': [],
    'installable': False,
    'auto_install': False,
}
