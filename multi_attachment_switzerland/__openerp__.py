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
#    @author: Michael Sandoz <sandozmichael@hotmail.com>
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
    'name': "multi_attachment_switzerland",
    'summary': """ Upload multi-attachment""",
    'description': """ Upload multi-attachment:
         - specify in qweb.xml models where multiple selection is possible
         - sync_mail_multi_attach module must be in addons on server
           https://www.odoo.com/apps/modules/8.0/sync_mail_multi_attach/""",
    'author': "Michael Sandoz",
    'website': "http://www.compassion.ch",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/
    # module/module_data.xml
    # for the full list
    'category': 'Social Network',
    'version': '0.1',

    # WARNING sync_mail_multi_attach module necessary for this one
    # to work correctly
    'depends': ['sync_mail_multi_attach'],
    'qweb': ['static/src/xml/qweb.xml'],
}
