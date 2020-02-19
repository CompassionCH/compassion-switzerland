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
#    Copyright (C) 2017 Compassion CH (http://www.compassion.ch)
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
    'name': 'Compassion CH - HR Management',
    'version': '11.0.0.0.0',
    'license': 'AGPL-3',
    'category': 'HR',
    'author': 'Emanuel Cino',
    'website': 'http://www.compassion.ch',
    'data': [
        'views/hr_expense_custom.xml',
        'views/res_users_view.xml',
        'views/hr_payslip_view.xml',
        'data/hr_config.xml'
    ],
    'depends': [
        'hr_expense',                   # source/addons
        'hr_payroll',                   # source/addons
        'asterisk_click2dial',          # oca_addons/connector-telephony
        'web_notify',                   # oca_addons/web
        'hr_attendance_management',     # compassion-modules
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
