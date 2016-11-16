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
    'name': 'Upgrade Partners for Compassion Suisse',
    'version': '8.0.3.0',
    'category': 'Partner',
    'sequence': 150,
    'author': 'Compassion CH',
    'website': 'http://www.compassion.ch',
    'depends': [
        'sbc_compassion', 'mail_sendgrid', 'partner_contact_birthdate',
        'partner_firstname', 'geoengine_base_geolocalize',
        'geoengine_geoname_geocoder', 'mail_restrict_follower_selection',
    ],
    'data': [
        'data/partner_category_data.xml',
        'data/partner_title_data.xml',
        'data/geocode_cron.xml',
        'data/follower_restriction_rules.xml',
        'view/partner_compassion_view.xml',
        'view/bulk_encode_view.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
}
