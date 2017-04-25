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
#    Copyright (C) 2014 Compassion CH (http://www.compassion.ch)
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
    'name': 'OpenERP MySQL Connector',
    'version': '8.0.1',
    'category': 'Other',
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': [],
    'external_dependencies': {
        'python': ['MySQLdb'],
    },
    'description': """
OpenERP MySQL Connector
=========================

Utility module that enables other modules that depends on it to access a
MySQL server that is defined a settings screen.


Installation
============

To install this module, you need to install dependencies:

* requires python-MySQLdb to be installed on the server.

Configuration
=============

To configure this module, you need to add settings in .conf file of Odoo:

* mysql_host = <mysql host>
* mysql_db = <mysql database>
* mysql_user = <mysql user>
* mysql_pw = <mysql password>

Usage
=====

You can use this module directly from code:

* from mysql_connector.model.mysql_connector import mysql_connector
* con = mysql_connector()
* res_query = mysql_connector.selectAll(sql, args)
* mysql_connector.upsert(table, vals)

See file mysql_connector.py for all supported methods. You can as well
inherit to expand the functionalities.

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>
""",
    'data': [],
    'demo': [],
    'installable': False,
    'auto_install': False,
}
