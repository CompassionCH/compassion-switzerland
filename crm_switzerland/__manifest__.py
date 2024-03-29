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

# pylint: disable=C8101
{
    "name": "CRM additions for Compassion CH",
    "version": "12.0.1.0.0",
    "category": "CRM",
    "sequence": 150,
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "depends": [
        "crm_phone",  # oca_addons/connector_telephony
        "crm_request",  # compassion_modules/crm_request
        "crm_compassion",  # compassion_modules/crm_compassion
        "partner_compassion",  # compassion_switzerland/partner_compassion
        "report_compassion",  # compassion_switzerland/report_compassion
        "im_livechat"
    ],
    "data": [
        "views/crm_phonecall.xml",
        "views/calendar_event.xml",
        "views/res_users_view.xml",
        "views/interaction_resume_view.xml",
    ],
    "demo": [],
    "installable": True,
    "auto_install": False,
}
