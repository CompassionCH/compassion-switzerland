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
    'name': 'Sync Compassion Sponsorships with GP',
    'version': '1.5',
    'category': 'Other',
    'description': """
Sync Compassion Sponsorships with GP
====================================

This module syncs all contracts with GP so that the information can be seen
from GP.

Installation
============

To install this module, you need to install dependencies:

* requires python-MySQLdb to be installed on the server.

Configuration
=============

To configure this module, you need to add settings in .conf file of Odoo:

* mysql_host = <mysql host of gp>
* mysql_db = <mysql database of gp>
* mysql_user = <mysql user of gp>
* mysql_pw = <mysql password of gp>

Credits
=======

Contributors
------------

* Emanuel Cino <ecino@compassion.ch>
    """,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': ['child_sync_gp',
                'sponsorship_switzerland',
                'account_voucher',
                ],
    'data': ['workflow/sds_workflow.xml'],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
