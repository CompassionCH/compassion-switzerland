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
#    Copyright (C) 2020 Compassion CH (http://www.compassion.ch)
#    @author: Quentin Gigon, Sylvain Losey
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
    "name": "Crowdfunding Compassion",
    "version": "12.0.1.0.0",
    "author": "Compassion CH",
    "license": "AGPL-3",
    "website": "http://www.compassion.ch",
    "depends": [
        "cms_form_compassion",      # compassion-modules
        "theme_crowdfunding",       # compassion-switzerland
        "sponsorship_switzerland",  # compassion-switzerland
        "crm_compassion",           # compassion-modules
        "event",                    # odoo base modules
    ],
    "data": [
        "data/crowdfunding_website.xml",
        "data/crowdfunding_event_type.xml",
        "data/project_confirmation_email.xml",
        "data/product.xml",
        "security/ir.model.access.csv",
        "views/crowdfunding_project_settings.xml",
        "security/ir.model.access.csv",
        "views/homepage.xml",
        "views/crowdfunding_components.xml",
        "views/crowdfunding_participant_view.xml",
        "views/crowdfunding_project_view.xml",
        "views/product_template_view.xml",
        "views/projects_list_page.xml",
        "views/project_creation_page.xml",
        "views/project_page.xml",
        "views/project_donation_page.xml",
        "views/project_donation_form_page.xml",
        "views/progress_bar.xml",
    ],
    "demo": [
        "demo/demo.xml"
    ],
    "installable": True,
    "auto_install": False,
}
