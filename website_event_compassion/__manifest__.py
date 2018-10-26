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
    'name': 'Compassion Events Website',
    'version': '10.0.1.1.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'https://github.com/CompassionCH/compassion-modules/tree/10.0',
    'depends': [
        'website_compassion', 'crm_compassion', 'event', 'partner_compassion',
        'cms_form_compassion', 'payment_ogone_compassion'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/access_rules.xml',
        'data/event_type.xml',
        'views/event_compassion_open_wizard.xml',
        'views/event_compassion_view.xml',
        'views/event_event_view.xml',
        'views/event_registration_view.xml',
        'templates/assets.xml',
        'templates/event_page.xml',
        'templates/events_list.xml',
        'templates/event_registration.xml',
        'templates/participants_list.xml',
        'templates/participant_page.xml',
        'templates/donation_result.xml',
    ],
    'development_status': 'Beta',
    'installable': True,
    'auto_install': False,
}
