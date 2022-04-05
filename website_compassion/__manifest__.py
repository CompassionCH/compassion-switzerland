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
#    Copyright (C) 2018-2020 Compassion CH (http://www.compassion.ch)
#    @author: Sebastien Toth <popod@me.com>
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
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

# pylint: disable=C8101
{
    "name": "Compassion Website",
    "version": "12.0.1.0.1",
    "category": "Website",
    "author": "Sebastien Toth",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "data": [
        "security/access_rules.xml",
        "security/ir.model.access.csv",
        "template/my_account_components.xml",
        "template/my_account_personal_info.xml",
        "template/my_account_donations.xml",
        "template/my_account_my_children.xml",
        "template/my_account_write_a_letter.xml",
        "template/my_account_contact_us.xml",
        "template/survey_templates.xml",
        "template/login_template.xml",
        "template/form_widgets.xml",
        "data/livechat_channels.xml",
        'views/auth_signup.xml',
        "views/correspondence_template_view.xml",
        "views/robots.xml",
        "views/header.xml",
    ],
    "depends": [
        "partner_communication_switzerland",
        "password_security",
        "im_livechat"
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
