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
    'version': '10.0.2.0.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'https://github.com/CompassionCH/compassion-modules/tree/10.0',
    'depends': [
        'website_compassion', 'crm_compassion', 'event',
        'partner_communication_switzerland',
        'payment_ogone_compassion', 'survey_phone'
    ],
    'external_dependencies': {
        'python': ['magic'],
    },
    'data': [
        'security/ir.model.access.csv',
        'security/access_rules.xml',
        'data/event_type.xml',
        'data/event_registration_stage.xml',
        'data/event_registration_task.xml',
        'data/product.xml',
        'data/group_visit_emails.xml',
        'data/communication_config.xml',
        'data/survey.xml',
        'data/event_message_subtype.xml',
        'views/event_compassion_open_wizard.xml',
        'views/event_compassion_view.xml',
        'views/event_event_view.xml',
        'views/event_registration_view.xml',
        'views/registration_stage_view.xml',
        'views/registration_task_view.xml',
        'views/event_faq_view.xml',
        'views/res_vaccine_view.xml',
        'views/advocate_details.xml',
        'views/event_info_party_wizard.xml',
        'views/event_flight_view.xml',
        'views/event_type_view.xml',
        'templates/assets.xml',
        'templates/event_page.xml',
        'templates/events_list.xml',
        'templates/event_registration.xml',
        'templates/participants_list.xml',
        'templates/participant_page.xml',
        'templates/donation_result.xml',
        'templates/event_faq.xml',
        'templates/group_visit_step2.xml',
        'templates/group_visit_medical_info.xml',
        'templates/group_visit_practical_information.xml',
        'templates/group_visit_party_invitation.xml',
        'templates/robots.xml',
        'wizards/event_registration_communication_wizard.xml',
    ],
    'demo': [
        'demo/crm_event_demo.xml'
    ],
    'development_status': 'Beta',
    'installable': True,
    'auto_install': False,
}
