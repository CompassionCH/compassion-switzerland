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
#    Copyright (C) 2016 Compassion CH (http://www.compassion.ch)
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
    'name': 'Compassion CH Partner Communications',
    'version': '10.0.1.0.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['report_compassion', 'gift_compassion'],
    'external_dependencies': {
        'python': ['wand', 'detectlanguage', 'sendgrid']
    },
    'data': [
        'data/end_year_communication.xml',
        'data/major_revision_emails.xml',
        'data/child_letter_emails.xml',
        'data/lifecycle_emails.xml',
        'data/project_lifecycle_emails.xml',
        'data/other_emails.xml',
        'data/sponsorship_planned_emails.xml',
        'data/donation_emails.xml',
        'data/manual_emails.xml',
        'data/communication_config.xml',
        'data/sponsorship_communications_cron.xml',
        'data/default_communication.xml',
        'data/ir.advanced.translation.csv',
        'data/label_print.xml',
        'report/child_picture.xml',
        'views/communication_job_view.xml',
        'views/download_child_pictures_view.xml',
        'views/end_contract_wizard_view.xml',
        'views/disaster_alert_view.xml',
        'views/partner_compassion_view.xml',
        'views/change_text_wizard_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
