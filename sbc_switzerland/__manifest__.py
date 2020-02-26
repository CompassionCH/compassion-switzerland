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
#    @author: Roman Zoller, Emanuel Cino, Michaël Sandoz
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
    'name': 'Sponsor to beneficiary email communication',
    'version': '11.0.0.0.0',
    'category': 'Other',
    'author': 'Compassion CH',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'depends': [
        'mysql_connector',                      # compassion-switzerland
        'partner_communication_switzerland',    # compassion-switzerland
        'child_switzerland'                     # compassion-switzerland
    ],
    'external_dependencies': {
        'python': ['smb', 'PyPDF2', 'pysftp', 'wand']
    },
    'data': [
        'security/ir.model.access.csv',
        'data/scan_letter_params.xml',
        'data/import_config_templates.xml',
        'data/nas_parameters.xml',
        'data/local_letters_cron.xml',
        'data/translator_email.xml',
        'data/communication_config.xml',
        'data/translator_server_actions.xml',
        'data/translator_action_rules.xml',
        'data/communication_config.xml',
        'views/import_config_view.xml',
        'views/import_letters_history_view.xml',
        'views/correspondence_view.xml',
        'views/s2b_generator_view.xml',
        'views/advocate_view.xml',
        'reports/translation_reports_view.xml',
    ],
    'demo': [],
    'installable': True,
}
