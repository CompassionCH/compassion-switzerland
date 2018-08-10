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
#    Copyright (C) 2014-2018 Compassion CH (http://www.compassion.ch)
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

# pylint: disable=C8101
{
    'name': 'Upgrade Partners for Compassion Suisse',
    'version': '10.0.1.5.0',
    'category': 'Partner',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': [
        'sbc_compassion',
        'thankyou_letters',
        'mail_sendgrid',
        'partner_contact_birthdate',
        'account_banking_mandate',
        'geoengine_partner',
        'base_geolocalize',
        'web_notify',
        'partner_survey',
        'website_partner',
    ],
    'external_dependencies': {
        'python': ['pandas', 'pyminizip']
    },
    'data': [
        'security/ir.model.access.csv',
        'data/partner_category_data.xml',
        'data/partner_title_data.xml',
        'data/ambassador_engagement_data.xml',
        'data/calendar_event_type.xml',
        'data/ir_cron.xml',
        'views/ambassador_details.xml',
        'views/partner_compassion_view.xml',
        'views/product_view.xml',
        'views/partner_check_double.xml',
        'views/notification_settings_view.xml',
    ],
    'installable': True,
    'auto_install': False,
}
