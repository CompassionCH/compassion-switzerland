# -*- coding: utf-8 -*-
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
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# pylint: disable=C8101
{
    'name': 'Muskathlon',
    'version': '10.0.3.1.0',
    'category': 'Reports',
    'author': 'Sebastien Toth',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'data': [
        'security/ir.model.access.csv',
        'security/access_rules.xml',
        'data/default_sports.xml',
        'data/res_users.xml',
        'data/survey_muskathlon_medical_infos.xml',
        'data/product.xml',
        'data/event_type.xml',
        'data/event_registration_stage.xml',
        'data/event_registration_task.xml',
        'reports/muskathlon_view.xml',
        'views/event_compassion_view.xml',
        'views/partner_compassion_view.xml',
        'views/recurring_contracts_view.xml',
        'views/muskathlon_registrations.xml',
        'views/notification_settings_view.xml',
        'views/payment_transaction_view.xml',
        'views/advocate_details.xml',
        'templates/muskathlon_details.xml',
        'templates/muskathlon_my_details.xml',
        'templates/muskathlon_my_home.xml',
        'templates/muskathlon_participant_details.xml',
        'templates/muskathlon_registration_form.xml',
        'templates/muskathlon_views.xml',
        'templates/muskathlon_order_material.xml',
        'templates/assets.xml'
    ],
    'depends': ['website_event_compassion', 'survey'],
    'external_dependencies': {
        'python': ['magic'],
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
}
