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
#    Copyright (C) 2014-2015 Compassion CH (http://www.compassion.ch)
#    @author: Emmanuel Mathier <emmanuel.mathier@gmail.com>
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
    'name': "SBC sync - Import spoken languages",
    'version': '0.1',
    'category': 'Other',
    'summary': """
        SBC - Import spoken_langs sync GP""",
    'sequence': 150,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'description': """
Sync spoken languages with GP
================================

This module syncs all spoken languages from countries and partners with GP.

Configuration
=============

To configure this module, you need to add settings in .conf file of Odoo:

* mysql_host = <mysql host of gp>
* mysql_db = <mysql database of gp>
* mysql_user = <mysql user of gp>
* mysql_pw = <mysql password of gp>
* smb_user = <samba user for pushing child pictures on the NAS>
* smb_pwd = <samba password>
* smb_ip = <IP Address of the NAS>
* smb_port = <Samba Port>
* gp_pictures = <Path to the folder of child pictures on the NAS>
    """,
    'depends': ['base', 'base_location', 'sbc_compassion', 'mysql_connector'],
    'data': [
        'view/sbc_sync_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
