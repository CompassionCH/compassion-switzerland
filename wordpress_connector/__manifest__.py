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
#    Copyright (C) 2016-2017 Compassion CH (http://www.compassion.ch)
#    @author: Philippe Heer <heerphilippe@msn.com>, Emanuel Cino
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
    'name': 'Compassion CH Wordpress Connector',
    'version': '10.0.1.0.0',
    'category': 'Social',
    'author': 'Emanuel Cino',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'data': [
        'views/import_letter_view.xml',
        'views/request.xml',
    ],
    'depends': ['mass_mailing_switzerland', 'child_sync_wp',
                'cms_form_compassion', 'sbc_switzerland', 'crm_compassion',
                'crm_request'],
    'external_dependencies': {
        'python': ['pysftp']
    },
    'demo': [],
    'installable': True,
    'auto_install': True,
}
