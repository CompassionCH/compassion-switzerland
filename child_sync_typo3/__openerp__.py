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
#    Copyright (C) 2015 Compassion CH (http://www.compassion.ch)
#    @author: David Coninckx <david@coninckx.com>
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
    'name': 'Sync Compassion Children with Typo3 website',
    'version': '8.0.1',
    'category': 'Other',
    'description': """
        This module manage upload of children
        and projects on the typo3 website.
    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['message_center_compassion'],
    'external_dependencies': {
        'python': ['pysftp'],
    },
    'data': [
        'view/child_on_typo3_wizard.xml',
        'view/child_remove_from_typo3.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
