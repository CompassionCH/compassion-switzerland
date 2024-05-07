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
#    Copyright (C) 2018 Compassion CH (http://www.compassion.ch)
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
    "name": "939 SMS Services",
    "version": "14.0.1.0.0",
    "category": "Other",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "https://github.com/CompassionCH/compassion-modules",
    "depends": [
        "sponsorship_switzerland",  # compassion-switzerland
        "child_sync_wp",  # compassion-switzerland
        "queue_job",  # OCA/queue,
        "sms",  # odoo
        "iap_alternative_provider",  # OCA/
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/sms_hook.xml",
        #        "data/sms_provider.xml",
        "views/sms_views.xml",
        "views/mail_message_view.xml",
        "views/sms_sms_view.xml",
        "views/iap_account_view.xml",
    ],
    "demo": ["demo/sms_hook.xml"],
    "development_status": "Beta",
    "installable": True,
    "auto_install": False,
}
