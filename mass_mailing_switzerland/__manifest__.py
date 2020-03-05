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
    'name': 'Mass Mailing Switzerland',
    'version': '11.0.0.0.0',
    'category': 'Mailing',
    'author': 'Emanuel Cino',
    'license': 'AGPL-3',
    'website': 'http://www.compassion.ch',
    'data': [
        'views/mass_mailing_view.xml',
        'views/mail_template_view.xml',
        'views/utm_view.xml',
        'views/contract_origin_view.xml',
        'views/mail_tracking_event_view.xml',
        'views/partner_view.xml',
        'views/account_invoice_line_view.xml',
        'data/refresh_sendgrid_tracking_cron.xml',
    ],
    'depends': [
        'mail_sendgrid_mass_mailing',           # oca_addons/social
        'partner_communication_switzerland',    # compassion-switzerland
        'cms_form_compassion'                   # compassion-modules
    ],
    'external_dependencies': {
        'python': ['pysftp']
    },
    'demo': [],
    'installable': True,
    'auto_install': False,
}
