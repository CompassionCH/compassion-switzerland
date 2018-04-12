# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-today OpenERP SA (<http://www.openerp.com>)
#    Copyright (C) 2011-today Synconics Technologies Pvt. Ltd.
#           (<http://www.synconics.com>)
#    Copyright (C) 2018-today Compassion Switzerland
#           (<http://www.compassion.ch>)
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
    "name": "Mail Multi Attachments",
    "version": "10.0.1.0.0",
    'author': 'Synconics Technologies Pvt. Ltd.',
    'license': 'AGPL-3',
    'website': 'https://www.synconics.com',
    "category": "Social Network",
    "summary": "Upload & Download multiple attachments in the mail at once",
    "depends": ["mail"],
    'data': ["views/mail_multi_attach.xml"],
    'qweb': ['static/src/xml/*.xml'],
    "installable": True,
    "auto_install": False
}
